from app.core.meta_stats import get_stat
from app.models.report import Report
from app.services.analysis.detail import data_source, indicator
from app.services.analysis.scorer import normalize, summary_for_score, weighted_sum


def calculate_noise_score(report: Report) -> int:
    if report.noise_score is not None:
        return report.noise_score
    indicators = _indicator_scores(report)
    return weighted_sum([(item["score"], item["weight"]) for item in indicators])


def get_noise_detail(report: Report) -> dict:
    score = calculate_noise_score(report)
    return {
        "score": score,
        "base_score": score,
        "summary": summary_for_score(score),
        "indicators": _indicator_scores(report),
        "visualization": {
            "type": "map_chart",
            "center": {"lat": report.lat, "lng": report.lng},
            "chart": _chart_data(report),
            "layers": [
                {"type": "ROAD", "name": "도로 소음", "source": "master_noise_road_fixed.csv"},
                {"type": "RAIL", "name": "철도 소음", "source": "master_noise_rail.csv"},
                {"type": "AIRCRAFT", "name": "항공 소음", "source": "master_noise_aircraft.csv"},
                {"type": "NOISE_PUB", "name": "생활 소음원", "source": "master_map_noise_pub_point.csv"},
                {"type": "NOISE_COMPLAINT", "name": "소음 민원", "source": "master_noise_complaint.csv"},
                {"type": "NOISE_MEASUREMENT", "name": "측정망 소음도", "source": "master_noise_measurement.csv"},
                {"type": "NOISE_HOURLY", "name": "시간대별 추정 소음", "source": "master_noise_hourly_lden.csv"},
                {"type": "NOISE_IDW_GRID", "name": "IDW 추정 소음", "source": "master_noise_idw_grid.csv"},
                {"type": "NOISE_LDEN", "name": "LDEN 장기 소음", "source": "master_noise_lden_point.csv"},
                {"type": "NOISE_TRAFFIC", "name": "교통량 소음", "source": "master_noise_traffic_point.csv"},
            ],
        },
        "data_source": data_source("도로/철도/항공/생활 소음원, 소음 민원, 시간대별 소음 추정 전처리 데이터 기반"),
    }


def _indicator_scores(report: Report) -> list[dict]:
    noise_pub_score = _score("noise_pub_density", report.noise_pub_density, inverse=True)
    noise_complaint_score = _score("noise_complaint", report.noise_complaint, inverse=True)
    noise_db_score = _score("noise_db", report.noise_db, inverse=True)
    road_noise_score = _score("noise_traffic_point", report.road_noise, inverse=True)
    aircraft_noise_score = _score("noise_aircraft", report.aircraft_noise, inverse=True)
    rail_noise_score = _score("noise_rail", report.rail_noise, inverse=True)
    noise_hourly_score = _score("noise_lden", report.noise_hourly, inverse=True)

    return [
        indicator(
            key="noise_pub_density",
            name="생활 소음원(유흥업소 등)",
            raw_value=report.noise_pub_density,
            unit="점",
            score=noise_pub_score,
            weight=0.15,
            display_value_override=_score_display(noise_pub_score),
        ),
        indicator(
            key="noise_complaint",
            name="소음 민원",
            raw_value=report.noise_complaint,
            unit="건",
            score=noise_complaint_score,
            weight=0.15,
        ),
        indicator(
            key="noise_db",
            name="측정망 소음도",
            raw_value=report.noise_db,
            unit="dB",
            score=noise_db_score,
            weight=0.20,
        ),
        indicator(
            key="road_noise",
            name="도로 소음",
            raw_value=report.road_noise,
            unit="점",
            score=road_noise_score,
            weight=0.15,
            display_value_override=_score_display(road_noise_score),
        ),
        indicator(
            key="aircraft_noise",
            name="항공기 소음",
            raw_value=report.aircraft_noise,
            unit="dB",
            score=aircraft_noise_score,
            weight=0.10,
        ),
        indicator(
            key="rail_noise",
            name="철도 소음",
            raw_value=report.rail_noise,
            unit="점",
            score=rail_noise_score,
            weight=0.10,
            display_value_override=_score_display(rail_noise_score),
        ),
        indicator(
            key="noise_hourly",
            name="시간대별 추정 소음",
            raw_value=report.noise_hourly,
            unit="dB",
            score=noise_hourly_score,
            weight=0.15,
        ),
    ]


def _score(key: str, value: float | int | None, *, inverse: bool = False) -> int | None:
    stat = get_stat(key)
    if not stat or value is None:
        return None
    return normalize(value, stat["p05"], stat["p95"], inverse=inverse)


def _score_display(score: int | None) -> str | None:
    return f"{score}점" if score is not None else None


def _chart_data(report: Report) -> dict:
    data = report.noise_table or {}
    return {
        "base_date_type": data.get("base_date_type", "HOURLY_AVERAGE"),
        "labels": data.get("labels", []),
        "values": data.get("values", []),
        "unit": "dB",
        "cached": True,
    }
