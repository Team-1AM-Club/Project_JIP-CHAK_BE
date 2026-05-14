from app.core.meta_stats import get_stat
from app.models.report import Report
from app.services.analysis.detail import data_source, indicator, indicator_chart
from app.services.analysis.scorer import clamp_score, normalize, weighted_sum


def calculate_flood_score(report: Report) -> int:
    flood_map = report.flood_map or {}
    if report.flood_score is not None and not flood_map.get("flood_defense"):
        return report.flood_score
    indicators = _indicator_scores(report)
    return weighted_sum([(item["score"], item["weight"]) for item in indicators])


def get_flood_detail(report: Report) -> dict:
    score = calculate_flood_score(report)
    indicators = _indicator_scores(report)
    flood_map = report.flood_map or {}
    return {
        "score": score,
        "base_score": score,
        "summary": _summary(score, flood_map),
        "indicators": indicators,
        "visualization": {
            "type": "flood_detail",
            "center": {"lat": report.lat, "lng": report.lng},
            "chart": indicator_chart(indicators),
            "flood_defense": _flood_defense_chart(flood_map),
            "flood_history": _flood_history_chart(flood_map),
            "layers": [],
        },
        "data_source": data_source("방재력, 최근 침수 이력, 불투수면적률 전처리 데이터 기반"),
    }


def _indicator_scores(report: Report) -> list[dict]:
    flood_map = report.flood_map or {}
    defense = flood_map.get("flood_defense") or {}
    history = flood_map.get("flood_history") or {}

    defense_score = _int_or_none(defense.get("score"))
    history_score = _history_score(history)
    impervious_score = _int_or_none(defense.get("score_imperv"))
    if impervious_score is None:
        impervious_score = _score("flood_imperv_proxy", report.impervious_ratio, inverse=True)

    return [
        _indicator_with_status(
            key="flood_defense",
            name="방재력",
            raw_value=defense_score,
            display_value_override=_score_display(defense_score),
            unit="score",
            score=defense_score,
            weight=0.50,
        ),
        _indicator_with_status(
            key="flood_history",
            name="최근 침수 이력",
            raw_value=history.get("total_count", 0),
            display_value_override=_history_total_display(history),
            unit="건",
            score=history_score,
            weight=0.30,
        ),
        _indicator_with_status(
            key="impervious_ratio",
            name="불투수면적률",
            raw_value=report.impervious_ratio,
            display_value_override=_percent_display(report.impervious_ratio),
            unit="%",
            score=impervious_score,
            weight=0.20,
        ),
    ]


def _flood_defense_chart(flood_map: dict) -> dict | None:
    defense = flood_map.get("flood_defense")
    if not defense:
        return None
    score = _int_or_none(defense.get("score"))
    top_percent = defense.get("top_percent")
    return {
        "title": "방재력",
        "score": score,
        "status": _status(score),
        "gu_average": defense.get("gu_average"),
        "percentile_label": f"상위 {top_percent}%" if top_percent is not None else None,
        "metrics": [
            {
                "key": "elevation",
                "label": "해발 고도",
                "value": defense.get("avg_elevation_m"),
                "display_value": _meter_display(defense.get("avg_elevation_m")),
                "sub_value": None,
                "sub_display_value": None,
                "score": _int_or_none(defense.get("score_elevation")),
                "status": _status(defense.get("score_elevation")),
            },
            {
                "key": "pump_capacity",
                "label": "배수펌프 용량",
                "value": defense.get("total_pump_m3"),
                "display_value": _pump_capacity_display(defense.get("total_pump_m3")),
                "sub_value": defense.get("pump_efficiency"),
                "sub_display_value": _pump_efficiency_display(defense.get("pump_efficiency")),
                "score": _int_or_none(defense.get("score_pump")),
                "status": _status(defense.get("score_pump")),
            },
            {
                "key": "impervious_ratio",
                "label": "불투수면적률",
                "value": defense.get("imperv_proxy"),
                "display_value": _percent_display(defense.get("imperv_proxy")),
                "sub_value": None,
                "sub_display_value": None,
                "score": _int_or_none(defense.get("score_imperv")),
                "status": _status(defense.get("score_imperv")),
            },
        ],
    }


def _flood_history_chart(flood_map: dict) -> dict | None:
    history = flood_map.get("flood_history")
    if not history:
        return None
    total_count = round(_float_or_zero(history.get("total_count")))
    gu_average = history.get("gu_average")
    period = str(history.get("period") or history.get("data_year") or 2025)
    return {
        "title": "최근 침수 이력",
        "period": period,
        "total_count": total_count,
        "display_total": f"{total_count}건 / {period}년",
        "gu_average": gu_average,
        "average_label": _average_label(total_count, gu_average),
        "years": _single_year_history(period, history.get("years") or [], total_count),
        "events": [
            {
                "year": event.get("year"),
                "label": _event_label(event),
                "type": event.get("flood_type"),
                "area_m2": event.get("area_m2"),
                "depth_cm": event.get("depth_cm"),
            }
            for event in (history.get("events") or [])
        ],
    }


def _summary(score: int, flood_map: dict) -> str:
    defense = flood_map.get("flood_defense") or {}
    history = flood_map.get("flood_history") or {}
    total_count = round(_float_or_zero(history.get("total_count")))
    imperv = defense.get("imperv_proxy")
    if score >= 80:
        return "방재력과 최근 침수 이력이 모두 양호해 침수 위험이 낮은 편입니다."
    if score >= 60:
        return "방재력은 전반적으로 양호하지만 폭우 시 배수 상태와 최근 침수 이력을 함께 확인하는 것이 좋습니다."
    if total_count > 0 and imperv is not None:
        return "최근 침수 이력과 불투수면적률을 고려할 때 폭우 시 배수 상태를 미리 점검하는 것이 좋습니다."
    return "방재력, 불투수면적률, 최근 침수 이력을 기준으로 침수 위험을 분석했습니다."


def _indicator_with_status(**kwargs) -> dict:
    item = indicator(**kwargs)
    item["status"] = _status(item["score"])
    return item


def _history_score(history: dict) -> int:
    if not history:
        return 100
    count = _float_or_zero(history.get("total_count"))
    average = history.get("gu_average")
    if count <= 0:
        return 100
    if average is None or float(average) <= 0:
        return clamp_score(100 - count * 10)
    return clamp_score(100 - (count / float(average)) * 35)


def _score(key: str, value: float | int | None, *, inverse: bool = False) -> int | None:
    stat = get_stat(key)
    if not stat or value is None:
        return None
    return normalize(value, stat["p05"], stat["p95"], inverse=inverse)


def _single_year_history(period: str, years: list[dict], total_count: int) -> list[dict]:
    year = _period_year(period)
    for item in years:
        if item.get("year") == year:
            return [{"year": year, "count": int(item.get("count") or 0)}]
    return [{"year": year, "count": total_count}]


def _period_year(period: str) -> int:
    try:
        return int(str(period).split("-")[-1])
    except ValueError:
        return 2025


def _event_label(event: dict) -> str:
    year = event.get("year")
    flood_type = event.get("flood_type") or "침수"
    area = event.get("area_m2")
    parts = [f"{year}년" if year else "연도 미상", f"{flood_type} 침수"]
    if area is not None:
        parts.append(f"침수면적 {round(float(area), 1)}㎡")
    return " · ".join(parts)


def _average_label(total_count: int, gu_average) -> str | None:
    if gu_average is None:
        return None
    average = float(gu_average)
    direction = "낮음" if total_count <= average else "높음"
    return f"자치구 평균 {average:.1f}건보다 {direction}"


def _history_total_display(history: dict) -> str:
    period = str(history.get("period") or history.get("data_year") or 2025)
    return f"{round(_float_or_zero(history.get('total_count')))}건 / {period}년"


def _status(score) -> str:
    value = _int_or_none(score)
    if value is None:
        return "분석중"
    if value >= 80:
        return "안심"
    if value >= 60:
        return "양호"
    if value >= 40:
        return "주의"
    return "위험"


def _score_display(score: int | None) -> str:
    return "데이터 없음" if score is None else f"{score}점"


def _meter_display(value) -> str:
    if value is None:
        return "데이터 없음"
    return f"{_format_number(value)}m"


def _percent_display(value) -> str:
    if value is None:
        return "데이터 없음"
    return f"{_format_number(value)}%"


def _pump_capacity_display(value) -> str:
    if value is None:
        return "데이터 없음"
    return f"{_format_number(value, comma=True)}㎥/분"


def _pump_efficiency_display(value) -> str | None:
    if value is None:
        return None
    return f"효율 {_format_number(value)}%"


def _format_number(value, *, comma: bool = False) -> str:
    number = float(value)
    text = f"{number:.1f}".rstrip("0").rstrip(".")
    if comma:
        integer, _, decimal = text.partition(".")
        integer = f"{int(integer):,}"
        return f"{integer}.{decimal}" if decimal else integer
    return text


def _float_or_zero(value) -> float:
    return float(value) if value is not None else 0.0


def _int_or_none(value) -> int | None:
    return clamp_score(value) if value is not None else None
