# 불완전: 혼잡 상세 응답은 전처리 지표 기준으로 맞췄지만 세부값은 congestion_data JSON key 확정 전까지 fallback을 사용함.
from app.models.report import Report
from app.services.analysis.detail import data_source, indicator
from app.services.analysis.scorer import clamp_score, summary_for_score, weighted_sum


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
                {"type": "POPULATION", "name": "생활인구", "source": "master_congestion_population.csv"},
            ],
        },
        "data_source": data_source("생활인구, 버스·지하철 혼잡도, 시간대별 밀도 전처리 데이터 기반"),
    }


def _indicator_scores(report: Report) -> list[dict]:
    data = report.congestion_data or {}
    density = float(data.get("hourly_population_density", data.get("peak_index", 50)))
    transit_access = float(data.get("transit_access", 500))
    commute = float(data.get("commute_congestion", data.get("peak_index", 50)))
    delay_rate = float(data.get("average_delay_rate", 0))

    return [
        indicator(
            key="hourly_population_density",
            name="시간대별 인구 밀도",
            raw_value=density,
            unit="명",
            score=clamp_score(100 - density),
            weight=0.35,
        ),
        indicator(
            key="transit_access",
            name="대중교통 접근성",
            raw_value=transit_access,
            unit="m",
            score=clamp_score(100 - transit_access / 30),
            weight=0.20,
        ),
        indicator(
            key="commute_congestion",
            name="출퇴근 혼잡도",
            raw_value=commute,
            unit="%",
            score=clamp_score(100 - commute),
            weight=0.30,
        ),
        indicator(
            key="average_delay_rate",
            name="평균 지연율",
            raw_value=delay_rate,
            unit="%",
            score=clamp_score(100 - delay_rate * 3),
            weight=0.15,
        ),
    ]


def _chart_data(report: Report) -> dict:
    data = report.congestion_data or {}
    return {
        "base_date_type": data.get("base_date_type", "WEEKDAY_AVERAGE"),
        "labels": data.get("labels", []),
        "values": data.get("values", []),
        "unit": data.get("unit", "density_index"),
        "cached": True,
    }
