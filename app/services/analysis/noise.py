from app.core.meta_stats import get_stat
from app.models.report import Report
from app.services.analysis.detail import data_source, indicator, indicator_chart
from app.services.analysis.scorer import normalize, weighted_sum


def calculate_noise_score(report: Report) -> int:
    if report.noise_score is not None:
        return report.noise_score
    indicators = _indicator_scores(report)
    return weighted_sum([(item["score"], item["weight"]) for item in indicators])


def get_noise_detail(report: Report) -> dict:
    score = calculate_noise_score(report)
    indicators = _indicator_scores(report)
    return {
        "score": score,
        "base_score": score,
        "summary": _summary(score, report),
        "indicators": indicators,
        "visualization": {
            "type": "noise_detail",
            "center": {"lat": report.lat, "lng": report.lng},
            "chart": indicator_chart(indicators),
            "noise_source_chart": _noise_source_chart(report),
            "noise_hourly_chart": _noise_hourly_chart(report),
            "layers": [
                {"type": "NOISE_TRAFFIC", "name": "도로교통 소음", "source": "master_noise_traffic_point.csv"},
                {"type": "NOISE_COMPLAINT", "name": "소음 민원", "source": "master_noise_complaint.csv"},
                {"type": "NOISE_PUB", "name": "생활 소음원", "source": "master_map_noise_pub_point.csv"},
                {"type": "NOISE_MEASUREMENT", "name": "측정망 소음도", "source": "master_noise_measurement.csv"},
                {"type": "NOISE_HOURLY", "name": "시간대별 소음", "source": "master_noise_hourly_lden.csv"},
                {"type": "NOISE_IDW_GRID", "name": "주변 추정 소음", "source": "master_noise_idw_grid.csv"},
            ],
        },
        "data_source": data_source(
            "교통량 기반 도로소음, 자치구 소음 민원, 생활 소음원, 환경소음 측정망, 시간대별 소음 전처리 데이터 기반"
        ),
    }


def _indicator_scores(report: Report) -> list[dict]:
    table = report.noise_table or {}
    traffic = table.get("traffic") or {}
    measurement = table.get("measurement") or {}

    pub_count = report.noise_pub_density
    complaint = report.noise_complaint
    estimated_db = report.noise_db
    road_noise = report.road_noise
    measurement_leq = measurement.get("leq")

    pub_score = _pub_score(pub_count)
    complaint_score = _score("noise_complaint", complaint, inverse=True)
    estimated_db_score = _score("noise_idw_grid", estimated_db, inverse=True)
    road_noise_score = _score("noise_traffic_point", road_noise, inverse=True)
    measurement_score = _score("noise_measurement_leq", measurement_leq, inverse=True)

    traffic_display_value = _traffic_display(traffic, road_noise)

    return [
        indicator(
            key="noise_pub_density",
            name="생활 소음원",
            raw_value=pub_count,
            unit="곳",
            score=pub_score,
            weight=0.15,
        ),
        indicator(
            key="noise_complaint",
            name="소음 민원",
            raw_value=complaint,
            unit="건",
            score=complaint_score,
            weight=0.15,
        ),
        indicator(
            key="noise_db",
            name="주변 추정 소음도",
            raw_value=estimated_db,
            unit="dB",
            score=estimated_db_score,
            weight=0.25,
        ),
        indicator(
            key="road_noise",
            name="도로교통 소음",
            raw_value=road_noise,
            unit="대/일",
            score=road_noise_score,
            weight=0.20,
            display_value_override=traffic_display_value,
        ),
        indicator(
            key="measurement_noise",
            name="측정망 소음도",
            raw_value=measurement_leq,
            unit="dB",
            score=measurement_score,
            weight=0.25,
        ),
    ]


def _score(key: str, value: float | int | None, *, inverse: bool = False) -> int | None:
    stat = get_stat(key)
    if not stat or value is None:
        return None
    return normalize(value, stat["p05"], stat["p95"], inverse=inverse)


def _pub_score(count: float | int | None) -> int | None:
    if count is None:
        return None
    value = float(count)
    if value <= 0:
        return 100
    if value <= 2:
        return 80
    if value <= 5:
        return 65
    if value <= 10:
        return 45
    return 25


def _noise_source_chart(report: Report) -> dict:
    table = report.noise_table or {}
    traffic = table.get("traffic") or {}
    complaint = table.get("complaint") or {}
    pub = table.get("pub") or {}
    measurement = table.get("measurement") or {}

    return {
        "title": "소음원별 영향",
        "subtitle": "지표별 단위 다름",
        "items": [
            _traffic_item(report, traffic),
            _complaint_item(report, complaint),
            _pub_item(report, pub),
            _measurement_item(measurement),
        ],
    }


def _traffic_item(report: Report, traffic: dict) -> dict:
    score = _score("noise_traffic_point", report.road_noise, inverse=True)
    distance_m = _round_distance(traffic.get("distance_m"))
    return {
        "key": "traffic",
        "label": "도로교통 소음",
        "value": _round_value(traffic.get("daily_traffic") or report.road_noise),
        "display_value": _traffic_display(traffic, report.road_noise),
        "unit": "대/일",
        "status": _score_status(score),
        "description": "가까운 교통량 지점 기준",
        "source": "master_noise_traffic_point.csv",
        "distance_m": distance_m,
        "distance_label": _distance_label(distance_m),
        "meta": {
            "point_no": traffic.get("point_no"),
            "point_name": traffic.get("point_name"),
            "daily_traffic": _round_value(traffic.get("daily_traffic")),
            "night_traffic": _round_value(traffic.get("night_traffic")),
            "night_traffic_label": _traffic_label(traffic.get("night_traffic"), prefix="심야 "),
            "risk_score": _round_value(traffic.get("raw_score")),
        },
    }


def _complaint_item(report: Report, complaint: dict) -> dict:
    yearly = complaint.get("yearly_count")
    monthly = None if yearly is None else float(yearly) / 12
    score = _score("noise_complaint", report.noise_complaint, inverse=True)
    avg = complaint.get("seoul_average_yearly")
    diff_label = _average_diff_label(yearly, avg)
    return {
        "key": "complaint",
        "label": "소음 민원",
        "value": _round_value(monthly),
        "display_value": _monthly_label(monthly),
        "unit": "건/월",
        "status": _score_status(score),
        "description": diff_label or "자치구 연간 민원 월평균",
        "source": "master_noise_complaint.csv",
        "distance_m": None,
        "distance_label": None,
        "meta": {
            "gu_name": complaint.get("gu_name"),
            "yearly_count": _round_value(yearly),
            "seoul_average_yearly": _round_value(avg),
        },
    }


def _pub_item(report: Report, pub: dict) -> dict:
    score = _pub_score(report.noise_pub_density)
    radius_m = int(pub.get("radius_m") or 200)
    return {
        "key": "pub",
        "label": "유흥업소",
        "value": int(report.noise_pub_density or 0),
        "display_value": f"{int(report.noise_pub_density or 0)}곳",
        "unit": "곳",
        "status": _score_status(score),
        "description": f"반경 {radius_m}m 내",
        "source": "master_map_noise_pub_point.csv",
        "distance_m": None,
        "distance_label": None,
        "meta": {
            "radius_m": radius_m,
        },
    }


def _measurement_item(measurement: dict) -> dict:
    leq = measurement.get("leq")
    score = _score("noise_measurement_leq", leq, inverse=True)
    distance_m = _round_distance(measurement.get("distance_m"))
    return {
        "key": "measurement",
        "label": "측정망 소음도",
        "value": _round_value(leq),
        "display_value": _db_label(leq),
        "unit": "dB",
        "status": _score_status(score),
        "description": "가까운 환경소음 측정망 기준",
        "source": "master_noise_measurement.csv",
        "distance_m": distance_m,
        "distance_label": _distance_label(distance_m),
        "meta": {
            "station": measurement.get("station"),
            "land_use": measurement.get("land_use"),
            "address": measurement.get("address"),
        },
    }


def _noise_hourly_chart(report: Report) -> dict | None:
    table = report.noise_table or {}
    measurement = table.get("measurement") or {}
    hourly_rows = table.get("hourly") or []
    if not hourly_rows:
        return None

    by_hour = {_normalize_hour(row.get("hour")): row for row in hourly_rows}
    labels = [f"{hour:02d}" for hour in range(24)]
    values = [_round_value((by_hour.get(label) or {}).get("raw_score")) for label in labels]
    lden_values = [_round_value((by_hour.get(label) or {}).get("lden_score")) for label in labels]
    peak = _peak_point(labels, lden_values)
    night_average = _night_average(labels, values)
    distance_m = _round_distance(measurement.get("distance_m"))

    return {
        "title": "시간대별 평균 소음(dB)",
        "subtitle": "가까운 측정망 기준",
        "station": measurement.get("station"),
        "distance_m": distance_m,
        "distance_label": _distance_label(distance_m),
        "unit": "dB",
        "labels": labels,
        "values": values,
        "lden_values": lden_values,
        "statuses": [_db_status(value) for value in lden_values],
        "summary": {
            "peak": peak,
            "night_average": _round_value(night_average),
            "night_average_label": None if night_average is None else f"야간 평균 {_round_value(night_average)}dB",
        },
    }


def _summary(score: int, report: Report) -> str:
    table = report.noise_table or {}
    traffic = table.get("traffic") or {}
    measurement = table.get("measurement") or {}
    if score >= 80:
        return "주변 소음원이 적고 측정망 소음도도 낮아 비교적 조용한 생활 환경입니다."
    if score >= 60:
        return "전반적인 소음 여건은 양호하지만 도로교통이나 시간대별 소음은 확인이 필요합니다."
    if traffic or measurement:
        return "주변 교통량과 측정망 소음도를 기준으로 일부 시간대 소음 관리가 필요합니다."
    return "소음 민원과 생활 소음원 지표를 기준으로 주변 소음에 주의가 필요합니다."


def _traffic_display(traffic: dict, fallback) -> str | None:
    return _traffic_label(traffic.get("daily_traffic") or fallback)


def _traffic_label(value, *, prefix: str = "") -> str | None:
    rounded = _round_value(value)
    return None if rounded is None else f"{prefix}{rounded:,}대/일"


def _monthly_label(value) -> str | None:
    rounded = _round_value(value)
    return None if rounded is None else f"{rounded:,}건/월"


def _db_label(value) -> str | None:
    rounded = _round_value(value)
    return None if rounded is None else f"{rounded}dB"


def _distance_label(distance_m: int | None) -> str | None:
    if distance_m is None:
        return None
    if distance_m >= 1000:
        return f"{distance_m / 1000:.1f}km"
    return f"{distance_m}m"


def _average_diff_label(value, average) -> str | None:
    if value is None or average in (None, 0):
        return None
    diff = (float(value) - float(average)) / float(average) * 100
    direction = "↑" if diff >= 0 else "↓"
    return f"자치구 평균 대비 {abs(round(diff))}% {direction}"


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


def _db_status(value) -> str:
    if value is None:
        return "분석중"
    score = _score("noise_hourly_lden", value, inverse=True)
    return _score_status(score)


def _normalize_hour(value) -> str | None:
    if value is None:
        return None
    text = str(value).replace("시", "").strip()
    if not text:
        return None
    return f"{int(text):02d}"


def _peak_point(labels: list[str], values: list[float | int | None]) -> dict | None:
    pairs = [(label, value) for label, value in zip(labels, values) if value is not None]
    if not pairs:
        return None
    hour, value = max(pairs, key=lambda item: item[1])
    return {
        "hour": hour,
        "value": value,
        "display_value": _db_label(value),
    }


def _night_average(labels: list[str], values: list[float | int | None]) -> float | None:
    night_values = [
        float(value)
        for label, value in zip(labels, values)
        if value is not None and (int(label) <= 5 or int(label) >= 22)
    ]
    if not night_values:
        return None
    return sum(night_values) / len(night_values)


def _round_value(value) -> float | int | None:
    if value is None:
        return None
    rounded = round(float(value), 1)
    return int(rounded) if rounded.is_integer() else rounded


def _round_distance(value) -> int | None:
    return None if value is None else round(float(value))
