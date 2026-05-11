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
                {"type": "ROAD", "name": "도로 소음", "source": "master_noise_road.csv"},
                {"type": "RAIL", "name": "철도 소음", "source": "master_noise_rail.csv"},
                {"type": "AIRCRAFT", "name": "항공 소음", "source": "master_noise_aircraft.csv"},
                {"type": "NOISE_PUB", "name": "생활 소음원", "source": "master_noise_pub_converted.csv"},
            ],
        },
        "data_source": data_source("도로/철도/항공/생활 소음원, 소음 민원, 시간대별 소음 추정 전처리 데이터 기반"),
    }


def _indicator_scores(report: Report) -> list[dict]:
    return [
        indicator(
            key="noise_pub_density",
            name="생활 소음원(유흥업소 등)",
            raw_value=report.noise_pub_density,
            unit="점",
            score=_score("noise_pub_density", report.noise_pub_density, inverse=True),
            weight=0.15,
        ),
        indicator(
            key="noise_complaint",
            name="소음 민원",
            raw_value=report.noise_complaint,
            unit="건",
            score=_score("noise_complaint", report.noise_complaint, inverse=True),
            weight=0.15,
        ),
        indicator(
            key="noise_db",
            name="측정망 소음도",
            raw_value=report.noise_db,
            unit="dB",
            score=_score("noise_db", report.noise_db, inverse=True),
            weight=0.20,
        ),
        indicator(
            key="road_noise",
            name="도로 소음",
            raw_value=report.road_noise,
            unit="점",
            score=_score("noise_road", report.road_noise, inverse=True),
            weight=0.15,
        ),
        indicator(
            key="aircraft_noise",
            name="항공기 소음",
            raw_value=report.aircraft_noise,
            unit="dB",
            score=_score("noise_aircraft", report.aircraft_noise, inverse=True),
            weight=0.10,
        ),
        indicator(
            key="rail_noise",
            name="철도 소음",
            raw_value=report.rail_noise,
            unit="점",
            score=_score("noise_rail", report.rail_noise, inverse=True),
            weight=0.10,
        ),
        indicator(
            key="noise_hourly",
            name="시간대별 추정 소음",
            raw_value=report.noise_hourly,
            unit="dB",
            score=_score("noise_hourly", report.noise_hourly, inverse=True),
            weight=0.15,
        ),
    ]


def _score(key: str, value: float | int | None, *, inverse: bool = False) -> int | None:
    stat = get_stat(key)
    if not stat or value is None:
        return None
    return normalize(value, stat["p05"], stat["p95"], inverse=inverse)


def _chart_data(report: Report) -> dict:
    data = report.noise_table or {}
    return {
        "base_date_type": data.get("base_date_type", "HOURLY_AVERAGE"),
        "labels": data.get("labels", []),
        "values": data.get("values", []),
        "unit": "dB",
        "cached": True,
    }
