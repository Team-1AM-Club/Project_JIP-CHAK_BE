# 불완전: 소음 상세 응답은 전처리 지표 기준으로 맞췄지만 히트맵/시간대 평균은 noise_table JSON에 임시 의존함.
from app.models.report import Report
from app.services.analysis.detail import data_source, indicator
from app.services.analysis.scorer import clamp_score, summary_for_score, weighted_sum


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
                {"type": "NOISE_PUB", "name": "생활 소음원", "source": "master_noise_pub.csv"},
            ],
        },
        "data_source": data_source("도로·철도·항공·생활 소음원, 소음 민원, 시간대별 소음 추정 전처리 데이터 기반"),
    }


def _indicator_scores(report: Report) -> list[dict]:
    source_noise_score = clamp_score(100 - max(report.road_noise - 45, 0) * 2)
    heatmap_noise = _noise_table_value(report, "heatmap_noise", report.road_noise)
    heatmap_score = clamp_score(100 - max(heatmap_noise - 45, 0) * 2)
    hourly_noise = _noise_table_value(report, "hourly_average_noise", report.road_noise)
    hourly_score = clamp_score(100 - max(hourly_noise - 45, 0) * 2)

    return [
        indicator(
            key="source_noise_level",
            name="소음원별 소음도",
            raw_value=report.road_noise,
            unit="dB",
            score=source_noise_score,
            weight=0.40,
        ),
        indicator(
            key="noise_heatmap_level",
            name="주변 소음 히트맵",
            raw_value=heatmap_noise,
            unit="dB",
            score=heatmap_score,
            weight=0.30,
        ),
        indicator(
            key="hourly_average_noise",
            name="시간대별 평균 소음",
            raw_value=hourly_noise,
            unit="dB",
            score=hourly_score,
            weight=0.30,
        ),
    ]


def _noise_table_value(report: Report, key: str, default: float | int) -> float:
    data = report.noise_table or {}
    return float(data.get(key, default))


def _chart_data(report: Report) -> dict:
    data = report.noise_table or {}
    return {
        "base_date_type": data.get("base_date_type", "HOURLY_AVERAGE"),
        "labels": data.get("labels", []),
        "values": data.get("values", []),
        "unit": "dB",
        "cached": True,
    }
