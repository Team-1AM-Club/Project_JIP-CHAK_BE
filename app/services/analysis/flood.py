from app.core.meta_stats import get_stat
from app.models.report import Report
from app.services.analysis.detail import data_source, indicator
from app.services.analysis.scorer import clamp_score, normalize, summary_for_score, weighted_sum


def calculate_flood_score(report: Report) -> int:
    if report.flood_score is not None:
        return report.flood_score
    indicators = _indicator_scores(report)
    return weighted_sum([(item["score"], item["weight"]) for item in indicators])


def get_flood_detail(report: Report) -> dict:
    score = calculate_flood_score(report)
    return {
        "score": score,
        "base_score": score,
        "summary": summary_for_score(score),
        "indicators": _indicator_scores(report),
        "visualization": {
            "type": "map",
            "center": {"lat": report.lat, "lng": report.lng},
            "layers": [
                {"type": "FLOOD_PUMP", "name": "배수펌프 시설", "source": "master_flood_pump.csv"},
                {"type": "IMPERVIOUS", "name": "불투수면적률", "source": "master_flood_impervious.csv"},
                {"type": "FLOOD_TRACE", "name": "주변 침수 흔적 지도", "source": "master_flood_trace.geojson"},
            ],
            "data": report.flood_map,
        },
        "data_source": data_source("침수 흔적, 불투수면적률, 배수펌프 시설 전처리 데이터 기반"),
    }


def _indicator_scores(report: Report) -> list[dict]:
    flood_map = report.flood_map or {}
    in_flood_trace = bool(flood_map.get("in_flood_trace", False))

    return [
        indicator(
            key="pump_capacity",
            name="배수펌프 용량",
            raw_value=report.pump_cap,
            unit="㎥/분",
            score=_score("flood_pump", report.pump_cap),
            weight=0.40,
        ),
        indicator(
            key="impervious_ratio",
            name="불투수면적률",
            raw_value=report.impervious_ratio,
            unit="%",
            score=_score("flood_impervious", report.impervious_ratio, inverse=True),
            weight=0.40,
        ),
        indicator(
            key="flood_trace",
            name="주변 침수 흔적",
            raw_value=in_flood_trace,
            unit=None,
            score=60 if in_flood_trace else 100,
            weight=0.20,
        ),
    ]


def _score(key: str, value: float | int | None, *, inverse: bool = False) -> int | None:
    stat = get_stat(key)
    if not stat or value is None:
        return None
    return normalize(value, stat["p05"], stat["p95"], inverse=inverse)
