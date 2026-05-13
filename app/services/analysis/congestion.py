from app.core.meta_stats import get_stat
from app.models.report import Report
from app.services.analysis.detail import data_source, indicator
from app.services.analysis.scorer import clamp_score, normalize, summary_for_score, weighted_sum


def calculate_congestion_score(report: Report) -> int:
    if report.congestion_score is not None:
        return report.congestion_score
    indicators = _indicator_scores(report)
    return weighted_sum([(item["score"], item["weight"]) for item in indicators])


def get_congestion_detail(report: Report) -> dict:
    score = calculate_congestion_score(report)
    return {
        "score": score,
        "base_score": score,
        "summary": summary_for_score(score),
        "indicators": _indicator_scores(report),
        "visualization": {
            "type": "chart",
            "chart": _chart_data(report),
            "layers": [
                {"type": "BUS", "name": "버스 혼잡도", "source": "master_congestion_bus.csv"},
                {"type": "SUBWAY", "name": "지하철 혼잡도", "source": "master_congestion_subway.csv"},
                {"type": "POPULATION", "name": "생활인구", "source": "master_congestion_population_fixed.csv"},
            ],
        },
        "data_source": data_source("생활인구, 버스/지하철 혼잡도, 시간대별 밀도 전처리 데이터 기반"),
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


def _chart_data(report: Report) -> dict:
    data = report.congestion_data or {}
    return {
        "base_date_type": data.get("base_date_type", "WEEKDAY_AVERAGE"),
        "labels": data.get("labels", []),
        "values": data.get("values", []),
        "unit": data.get("unit", "density_index"),
        "cached": True,
    }
