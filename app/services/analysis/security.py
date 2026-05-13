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
                {"type": "CCTV_GROWTH", "name": "CCTV 증가율", "source": "master_security_cctv_growth.csv"},
                {"type": "CRIME", "name": "범죄 발생", "source": "master_security_crime.csv"},
                {"type": "STREET_LIGHT", "name": "가로등/보안등", "source": "master_security_light_blind.csv"},
                {"type": "POLICE", "name": "가까운 파출소", "source": "master_security_police_fixed.csv"},
                {"type": "POLICE_POP", "name": "경찰 인구비", "source": "master_security_police_pop.csv"},
                {"type": "SAFE_PATH", "name": "안심귀갓길", "source": "master_security_safepath_fixed.csv"},
            ],
            "data": report.safety_map,
        },
        "data_source": data_source("범죄 통계, CCTV, 보안등, 안심귀갓길, 경찰 시설 전처리 데이터 기반"),
    }


def _indicator_scores(report: Report) -> list[dict]:
    crime_score = _score("security_crime", report.crime_count, inverse=True)
    cctv_score = _score("security_cctv", report.cctv_count)
    cctv_growth_score = _score("security_cctv_growth", report.cctv_growth)
    light_blind_score = _score("security_light_blind", report.light_blind_ratio, inverse=True)
    safepath_score = _score("security_safepath", report.safepath_score)
    police_score = _score("security_police", report.police_count)

    return [
        indicator(
            key="crime_count",
            name="범죄 발생",
            raw_value=report.crime_count,
            unit="건",
            score=crime_score,
            weight=0.25,
        ),
        indicator(
            key="cctv_density",
            name="CCTV 수",
            raw_value=report.cctv_count,
            unit="개",
            score=cctv_score,
            weight=0.15,
        ),
        indicator(
            key="cctv_growth",
            name="CCTV 증가율",
            raw_value=report.cctv_growth,
            unit="%",
            score=cctv_growth_score,
            weight=0.10,
        ),
        indicator(
            key="light_blind_ratio",
            name="보안등 사각지대",
            raw_value=report.light_blind_ratio,
            unit="점",
            score=light_blind_score,
            weight=0.15,
            display_value_override=_score_display(light_blind_score),
        ),
        indicator(
            key="safepath_score",
            name="안심귀갓길",
            raw_value=report.safepath_score,
            unit="점",
            score=safepath_score,
            weight=0.15,
            display_value_override=_score_display(safepath_score),
        ),
        indicator(
            key="police_access",
            name="경찰 치안",
            raw_value=report.police_count,
            unit="점",
            score=police_score,
            weight=0.20,
            display_value_override=_score_display(police_score),
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


def _score_display(score: int | None) -> str | None:
    return f"{score}점" if score is not None else None
