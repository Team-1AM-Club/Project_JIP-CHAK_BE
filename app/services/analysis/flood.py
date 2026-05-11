# 불완전: 침수 상세 응답은 전처리 지표 기준으로 맞췄지만 불투수면적률은 현재 DB의 low_ratio에 임시 매핑함.
from app.models.report import Report
from app.services.analysis.detail import data_source, indicator
from app.services.analysis.scorer import clamp_score, summary_for_score, weighted_sum


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
                {
                    "type": "FLOOD_TRACE",
                    "name": "주변 침수 흔적 지도",
                    "source": "master_flood_trace.geojson",
                }
            ],
            "data": report.flood_map,
        },
        "data_source": data_source("침수 흔적, 불투수면적률, 배수펌프 시설 전처리 데이터 기반"),
    }


def _indicator_scores(report: Report) -> list[dict]:
    flood_history_score = clamp_score(100 - report.flood_hist * 25)
    altitude_score = clamp_score(50 + report.altitude)
    pump_score = clamp_score(report.pump_cap / 30)
    impervious_score = clamp_score(100 - report.low_ratio)
    trace_score = 100 if not report.flood_map else 70

    return [
        indicator(
            key="flood_history_5y",
            name="5년 침수 이력",
            raw_value=report.flood_hist,
            unit="건",
            score=flood_history_score,
            weight=0.35,
        ),
        indicator(
            key="altitude",
            name="고도",
            raw_value=report.altitude,
            unit="m",
            score=altitude_score,
            weight=0.20,
        ),
        indicator(
            key="pump_capacity",
            name="배수펌프 용량",
            raw_value=report.pump_cap,
            unit="㎥/분",
            score=pump_score,
            weight=0.20,
        ),
        indicator(
            key="impervious_ratio",
            name="불투수면적율",
            raw_value=report.low_ratio,
            unit="%",
            score=impervious_score,
            weight=0.15,
        ),
        indicator(
            key="flood_trace",
            name="주변 침수 흔적",
            raw_value=bool(report.flood_map),
            unit=None,
            score=trace_score,
            weight=0.10,
        ),
    ]
