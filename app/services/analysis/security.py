from app.core.meta_stats import get_stat
from app.models.report import Report
from app.services.analysis.detail import data_source, indicator
from app.services.analysis.scorer import clamp_score, normalize, summary_for_score, weighted_sum


def calculate_security_score(report: Report) -> int:
    if report.security_score is not None:
        return report.security_score
    indicators = _indicator_scores(report)
    return weighted_sum([(item["score"], item["weight"]) for item in indicators])


def get_security_detail(report: Report) -> dict:
    score = calculate_security_score(report)
    return {
        "score": score,
        "base_score": score,
        "summary": summary_for_score(score),
        "indicators": _indicator_scores(report),
        "visualization": {
            "type": "map",
            "center": {"lat": report.lat, "lng": report.lng},
            "layers": [
                {"type": "CCTV", "name": "주변 CCTV", "source": "master_security_cctv.csv"},
                {"type": "STREET_LIGHT", "name": "가로등/보안등", "source": "master_security_light_blind.csv"},
                {"type": "POLICE", "name": "가까운 파출소", "source": "master_security_police.csv"},
                {"type": "SAFE_PATH", "name": "안심귀갓길", "source": "master_security_safepath.csv"},
            ],
            "data": report.safety_map,
        },
        "data_source": data_source("범죄 통계, CCTV, 보안등, 안심귀갓길, 경찰 시설 전처리 데이터 기반"),
    }


def _indicator_scores(report: Report) -> list[dict]:
    return [
        indicator(
            key="crime_count",
            name="범죄 발생",
            raw_value=report.crime_count,
            unit="건",
            score=_score("security_crime", report.crime_count, inverse=True),
            weight=0.25,
        ),
        indicator(
            key="cctv_density",
            name="CCTV 수",
            raw_value=report.cctv_count,
            unit="개",
            score=_score("security_cctv", report.cctv_count),
            weight=0.15,
        ),
        indicator(
            key="cctv_growth",
            name="CCTV 증가율",
            raw_value=report.cctv_growth,
            unit="%",
            score=_score("security_cctv_growth", report.cctv_growth),
            weight=0.10,
        ),
        indicator(
            key="light_blind_ratio",
            name="보안등 사각지대",
            raw_value=report.light_blind_ratio,
            unit="점",
            score=_score("security_light_blind", report.light_blind_ratio, inverse=True),
            weight=0.15,
        ),
        indicator(
            key="safepath_score",
            name="안심귀갓길",
            raw_value=report.safepath_score,
            unit="점",
            score=_score("security_safepath", report.safepath_score),
            weight=0.15,
        ),
        indicator(
            key="police_access",
            name="경찰 치안",
            raw_value=report.police_count,
            unit="개",
            score=_score("security_police", report.police_count),
            weight=0.20,
        ),
    ]


def _score(
    key: str,
    value: float | int | None,
    *,
    inverse: bool = False,
    fallback: int | None = None,
) -> int | None:
    stat = get_stat(key)
    if not stat or value is None:
        return fallback
    return normalize(value, stat["p05"], stat["p95"], inverse=inverse)
