# 불완전: 의료 상세 응답은 전처리 지표 기준으로 맞췄지만 공공 응급실/의료인력은 기존 emer/doctor 컬럼에 임시 매핑함.
from app.models.report import Report
from app.services.analysis.detail import data_source, indicator
from app.services.analysis.scorer import clamp_score, summary_for_score, weighted_sum


def calculate_medical_score(report: Report) -> int:
    if report.medical_score is not None:
        return report.medical_score
    indicators = _indicator_scores(report)
    return weighted_sum([(item["score"], item["weight"]) for item in indicators])


def get_medical_detail(report: Report) -> dict:
    score = calculate_medical_score(report)
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
                    "type": "NIGHT_CLINIC",
                    "name": "야간운영 의료시설",
                    "source": "master_map_night_clinics_point.csv",
                },
                {"type": "PHARMACY", "name": "약국", "source": "master_map_pharmacy_point.csv"},
                {
                    "type": "PUBLIC_EMERGENCY",
                    "name": "공공의료기관 응급실",
                    "source": "preprocessed_public_er",
                },
            ],
            "data": report.medic_map,
        },
        "data_source": data_source("야간의료시설, 약국, 공공의료기관 응급실, 의료 인력 전처리 데이터 기반"),
    }


def _indicator_scores(report: Report) -> list[dict]:
    distance_score = clamp_score(100 - report.medic_dist / 30)
    night_score = clamp_score(report.nightopen_count * 10)
    er_score = clamp_score(report.emeropen_count * 35 + report.emer_cap)
    staff_score = clamp_score(report.doctor_ratio * 20)

    return [
        indicator(
            key="nearest_medical_distance",
            name="가까운 의료시설 거리",
            raw_value=report.medic_dist,
            unit="m",
            score=distance_score,
            weight=0.30,
        ),
        indicator(
            key="night_medical_density",
            name="야간운영 의료시설 밀도",
            raw_value=report.nightopen_count,
            unit="곳",
            score=night_score,
            weight=0.25,
        ),
        indicator(
            key="public_er_access",
            name="공공의료기관 응급실 접근성",
            raw_value=report.emeropen_count,
            unit="곳",
            score=er_score,
            weight=0.25,
        ),
        indicator(
            key="public_medical_staff",
            name="공공의료기관 의료 인력 현황",
            raw_value=report.doctor_ratio,
            unit="명/천명",
            score=staff_score,
            weight=0.20,
        ),
    ]
