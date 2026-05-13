from app.core.meta_stats import get_stat
from app.models.report import Report
from app.services.analysis.detail import data_source, indicator
from app.services.analysis.scorer import clamp_score, normalize, summary_for_score, weighted_sum


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
                {"type": "NIGHT_CLINIC", "name": "야간운영 의료시설", "source": "master_map_night_clinics_point_fixed.csv"},
                {"type": "PHARMACY", "name": "약국", "source": "master_map_pharmacy_point_converted.csv"},
                {"type": "HEALTH_WORKFORCE", "name": "의료 인력", "source": "master_health_workforce_gu.csv"},
            ],
            "data": report.medic_map,
        },
        "data_source": data_source("야간운영 의료시설, 약국, 의료 인력 전처리 데이터 기반"),
    }


def _indicator_scores(report: Report) -> list[dict]:
    return [
        indicator(
            key="night_medical_density",
            name="야간운영 병의원 수",
            raw_value=report.night_clinic,
            unit="개",
            score=_score("health_night_clinic", report.night_clinic),
            weight=0.35,
        ),
        indicator(
            key="pharmacy_density",
            name="주변 약국 수",
            raw_value=report.pharmacy_count,
            unit="개",
            score=_score("health_pharmacy", report.pharmacy_count),
            weight=0.35,
        ),
        indicator(
            key="public_medical_staff",
            name="구별 의료 인력 수",
            raw_value=report.medical_staff,
            unit="명",
            score=_score("health_workforce_gu", report.medical_staff),
            weight=0.30,
        ),
    ]


def _score(key: str, value: float | int | None, *, inverse: bool = False, fallback: int | None = None) -> int | None:
    stat = get_stat(key)
    if not stat or value is None:
        return fallback
    return normalize(value, stat["p05"], stat["p95"], inverse=inverse)
