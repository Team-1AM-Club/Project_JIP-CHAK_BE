# 불완전: 치안 상세 응답은 전처리 지표 기준으로 맞췄지만 검거율은 현재 DB 컬럼이 없어 중립값으로 임시 처리함.
from app.models.report import Report
from app.services.analysis.detail import data_source, indicator
from app.services.analysis.scorer import clamp_score, summary_for_score, weighted_sum


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
                {
                    "type": "STREET_LIGHT",
                    "name": "가로등·보안등",
                    "source": "master_security_light_blind.csv",
                },
                {"type": "POLICE", "name": "파출소·지구대", "source": "master_security_police.csv"},
                {"type": "SAFE_PATH", "name": "안심귀갓길", "source": "master_security_safepath.csv"},
            ],
            "data": report.safety_map,
        },
        "data_source": data_source("범죄 통계, CCTV, 보안등, 안심귀갓길, 경찰 시설 전처리 데이터 기반"),
    }


def _indicator_scores(report: Report) -> list[dict]:
    crime_count = sum(report.criminal_occur or [])
    crime_score = clamp_score(100 - crime_count / 2)
    arrest_rate_score = 70
    cctv_score = clamp_score(report.cctv_count * 5)
    light_score = clamp_score(report.lamp_count * 2)
    safepath_score = 70
    police_score = clamp_score(100 - report.police_dist / 30)

    return [
        indicator(
            key="crime_count_12m",
            name="최근 12개월 5대 범죄 발생수",
            raw_value=crime_count,
            unit="건",
            score=crime_score,
            weight=0.30,
        ),
        indicator(
            key="arrest_rate",
            name="검거율",
            raw_value=None,
            unit="%",
            score=arrest_rate_score,
            weight=0.15,
        ),
        indicator(
            key="cctv_density",
            name="CCTV 밀도",
            raw_value=report.cctv_count,
            unit="점",
            score=cctv_score,
            weight=0.20,
        ),
        indicator(
            key="light_density",
            name="가로등·보안등 밀도",
            raw_value=report.lamp_count,
            unit="점",
            score=light_score,
            weight=0.15,
        ),
        indicator(
            key="safepath_access",
            name="안심귀갓길 접근성",
            raw_value=None,
            unit="m",
            score=safepath_score,
            weight=0.10,
        ),
        indicator(
            key="police_distance",
            name="가까운 파출소 거리",
            raw_value=report.police_dist,
            unit="m",
            score=police_score,
            weight=0.10,
        ),
    ]
