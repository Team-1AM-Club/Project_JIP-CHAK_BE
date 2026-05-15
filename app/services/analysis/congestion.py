from app.core.meta_stats import get_stat
from app.models.report import Report
from app.services.analysis.detail import data_source, indicator, indicator_chart
from app.services.analysis.scorer import clamp_score, normalize, weighted_sum


def calculate_congestion_score(report: Report) -> int:
    if report.congestion_score is not None:
        return report.congestion_score
    indicators = _indicator_scores(report)
    return weighted_sum([(item["score"], item["weight"]) for item in indicators])


def get_congestion_detail(report: Report) -> dict:
    score = calculate_congestion_score(report)
    indicators = _indicator_scores(report)
    return {
        "score": score,
        "base_score": score,
        "summary": _summary(score, report),
        "indicators": indicators,
        "visualization": {
            "type": "congestion_detail",
            "center": {"lat": report.lat, "lng": report.lng},
            "chart": indicator_chart(indicators),
            "time_series_chart": _chart_data(report),
            "population_hourly_chart": _population_hourly_chart(report),
            "nearby_transport_chart": _nearby_transport_chart(report),
            "bus_hourly_chart": _bus_hourly_chart(report),
            "layers": [
                {"type": "BUS", "name": "버스 혼잡도", "source": "master_congestion_bus.csv"},
                {"type": "BUS_HOURLY", "name": "버스 시간대별 유동인구", "source": "master_bus_hourly_per_stop.csv"},
                {"type": "METRO", "name": "지하철 혼잡도", "source": "master_metro_congestion.csv"},
                {"type": "METRO_POPULATION", "name": "지하철 승하차", "source": "master_metro_population.csv"},
                {"type": "POPULATION_HOURLY", "name": "생활권 시간대별 생활인구", "source": "master_population_hourly_risk.csv"},
            ],
        },
        "data_source": data_source("생활권 시간대별 생활인구, 버스 정류장 이용량, 지하철 혼잡도와 승하차 전처리 데이터 기반"),
    }


def _indicator_scores(report: Report) -> list[dict]:
    data = report.congestion_data or {}
    density = data.get("hourly_population_density")
    bus = data.get("bus_congestion")
    commute = data.get("commute_congestion")
    density_score = _score("floating_population", density, inverse=True)
    bus_score = _score("bus_congestion", bus, inverse=True)
    commute_score = _score("subway_congestion", commute, inverse=True)

    return [
        indicator(
            key="hourly_population_density",
            name="시간대별 생활인구 밀도",
            raw_value=density,
            unit="명",
            score=density_score,
            weight=0.35,
        ),
        indicator(
            key="bus_congestion",
            name="버스 혼잡도",
            raw_value=bus,
            unit="점",
            score=bus_score,
            weight=0.35,
            display_value_override=_score_display(bus_score),
        ),
        indicator(
            key="commute_congestion",
            name="지하철 혼잡도",
            raw_value=commute,
            unit="%",
            score=commute_score,
            weight=0.30,
        ),
    ]


def _score(key: str, value: float | int | None, *, inverse: bool = False) -> int | None:
    stat = get_stat(key)
    if not stat or value is None:
        return None
    return normalize(value, stat["p05"], stat["p95"], inverse=inverse)


def _score_display(score: int | None) -> str | None:
    return f"{score}점" if score is not None else None


def _population_hourly_chart(report: Report) -> dict | None:
    detail = (report.congestion_data or {}).get("population_detail") or {}
    hourly = detail.get("hourly_pop") or {}
    if not hourly:
        return None
    labels = [f"{hour:02d}" for hour in range(6, 23)]
    values = [_round_value(hourly.get(label)) for label in labels]
    pairs = [(label, value) for label, value in zip(labels, values) if value is not None]
    morning = _peak_between(pairs, 6, 11)
    evening = _peak_between(pairs, 16, 20)
    night = _value_at(pairs, "22")
    return {
        "title": "시간대별 인구 밀도",
        "scope": "생활권 기준",
        "unit": "명",
        "labels": labels,
        "values": values,
        "statuses": [_density_status(value) for value in values],
        "summary": {
            "morning_peak": _summary_point(morning),
            "evening_peak": _summary_point(evening),
            "night": _summary_point(night),
        },
    }


def _nearby_transport_chart(report: Report) -> dict:
    data = report.congestion_data or {}
    return {
        "title": "가까운 대중교통",
        "subway": _subway_card(data.get("nearest_subway")),
        "bus": _bus_card(data.get("nearest_bus")),
    }


def _bus_hourly_chart(report: Report) -> dict | None:
    bus_hourly = (report.congestion_data or {}).get("bus_hourly") or {}
    hourly = bus_hourly.get("hourly_pop") or {}
    if not hourly:
        return None
    labels = [f"{hour:02d}" for hour in range(6, 23)]
    values = [_round_value(hourly.get(label)) for label in labels]
    pairs = [(label, value) for label, value in zip(labels, values) if value is not None]
    return {
        "title": "주변 버스정류장 시간대별 유동인구",
        "radius_m": bus_hourly.get("radius_m", 500),
        "unit": "명",
        "labels": labels,
        "values": values,
        "stop_count": int(bus_hourly.get("stop_count") or 0),
        "summary": {
            "peak": _summary_point(max(pairs, key=lambda item: item[1]) if pairs else None),
        },
    }


def _chart_data(report: Report) -> dict:
    data = report.congestion_data or {}
    return {
        "base_date_type": data.get("base_date_type", "WEEKDAY_AVERAGE"),
        "labels": data.get("labels", []),
        "values": data.get("values", []),
        "unit": data.get("unit", "density_index"),
        "cached": True,
    }


def _subway_card(subway: dict | None) -> dict | None:
    if not subway:
        return None
    distance_m = _round_distance(subway.get("distance_m"))
    return {
        "type": "subway",
        "station_name": subway.get("station_name"),
        "line_name": subway.get("line_name"),
        "distance_m": distance_m,
        "distance_label": _distance_label(distance_m),
        "travel_label": _walk_time_label(distance_m),
        "status": _congestion_status(subway.get("peak_congestion_total")),
        "daily_passengers_total": _round_value(subway.get("daily_passengers_total")),
        "daily_passengers_label": _people_label(subway.get("daily_passengers_total")),
        "daily_passengers_weekday": _round_value(subway.get("daily_passengers_weekday")),
        "daily_passengers_weekend": _round_value(subway.get("daily_passengers_weekend")),
        "avg_congestion_total": _round_value(subway.get("avg_congestion_total")),
        "avg_congestion_label": _percent_label(subway.get("avg_congestion_total")),
        "peak_congestion_total": _round_value(subway.get("peak_congestion_total")),
        "peak_congestion_label": _percent_label(subway.get("peak_congestion_total")),
    }


def _bus_card(bus: dict | None) -> dict | None:
    if not bus:
        return None
    distance_m = _round_distance(bus.get("distance_m"))
    score = _score("bus_congestion", bus.get("raw_score"), inverse=True)
    return {
        "type": "bus",
        "stop_name": bus.get("stop_name"),
        "stop_type": bus.get("stop_type"),
        "distance_m": distance_m,
        "distance_label": _distance_label(distance_m),
        "travel_label": _walk_time_label(distance_m),
        "status": _score_status(score),
        "daily_avg_usage": _round_value(bus.get("daily_avg_usage")),
        "daily_avg_usage_label": _people_label(bus.get("daily_avg_usage")),
        "congestion_score": score,
        "congestion_score_label": _score_display(score),
    }


def _summary(score: int, report: Report) -> str:
    subway = (report.congestion_data or {}).get("nearest_subway")
    if score >= 80:
        return "생활권 인구와 주변 대중교통 혼잡도가 낮아 이동 여건이 비교적 여유롭습니다."
    if score >= 60:
        return "생활권과 대중교통 혼잡도는 전반적으로 양호하지만 출퇴근 피크 시간대는 확인이 필요합니다."
    if subway:
        return "가까운 대중교통 접근성은 있으나 생활권 인구 또는 피크 혼잡도가 높아 시간대 조절이 필요합니다."
    return "생활권 인구와 대중교통 혼잡 지표를 기준으로 이동 혼잡에 주의가 필요합니다."


def _peak_between(pairs: list[tuple[str, float]], start_hour: int, end_hour: int) -> tuple[str, float] | None:
    filtered = [
        (hour, value)
        for hour, value in pairs
        if start_hour <= int(hour) <= end_hour
    ]
    return max(filtered, key=lambda item: item[1]) if filtered else None


def _value_at(pairs: list[tuple[str, float]], hour: str) -> tuple[str, float] | None:
    return next((item for item in pairs if item[0] == hour), None)


def _summary_point(point: tuple[str, float] | None) -> dict | None:
    if point is None:
        return None
    hour, value = point
    return {
        "hour": hour,
        "value": value,
        "display_value": _people_label(value),
    }


def _density_status(value) -> str:
    if value is None:
        return "분석중"
    score = _score("floating_population", value, inverse=True)
    return _score_status(score)


def _congestion_status(value) -> str:
    if value is None:
        return "분석중"
    if float(value) >= 80:
        return "혼잡"
    if float(value) >= 50:
        return "주의"
    return "양호"


def _score_status(score: int | None) -> str:
    if score is None:
        return "분석중"
    if score >= 80:
        return "안심"
    if score >= 60:
        return "양호"
    if score >= 40:
        return "주의"
    return "위험"


def _round_value(value) -> float | int | None:
    if value is None:
        return None
    rounded = round(float(value), 1)
    return int(rounded) if rounded.is_integer() else rounded


def _round_distance(value) -> int | None:
    return None if value is None else round(float(value))


def _distance_label(distance_m: int | None) -> str:
    if distance_m is None:
        return "거리 데이터 없음"
    if distance_m >= 1000:
        return f"{distance_m / 1000:.1f}km"
    return f"{distance_m}m"


def _walk_time_label(distance_m: int | None) -> str:
    if distance_m is None:
        return "확인 필요"
    minutes = max(1, round(distance_m / 67))
    return f"도보 {minutes}분"


def _people_label(value) -> str | None:
    rounded = _round_value(value)
    return None if rounded is None else f"{rounded:,}명"


def _percent_label(value) -> str | None:
    rounded = _round_value(value)
    return None if rounded is None else f"{rounded}%"
