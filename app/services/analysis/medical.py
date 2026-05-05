# 불완전: 의료 점수 계산 구조는 구현됐지만 실제 의료시설/응급시설 데이터 기준 산식 검증이 필요함.
from app.models.report import Report
from app.services.analysis.scorer import summary_for_score


def calculate_medical_score(report: Report) -> int:
    if report.medical_score is not None:
        return report.medical_score
    score = 55
    score += 20 if report.medic_dist <= 500 else 10 if report.medic_dist <= 1000 else 0
    score += min(report.nightopen_count * 3, 15)
    score += min(report.emeropen_count * 5, 10)
    return max(0, min(100, score))


def get_medical_detail(report: Report) -> dict:
    score = calculate_medical_score(report)
    return {
        "score": score,
        "base_score": score,
        "summary": summary_for_score(score),
        "indicators": [
            {"name": "의료시설 거리", "value": report.medic_dist, "status": "양호" if report.medic_dist <= 1000 else "주의"},
            {"name": "야간 운영 시설", "value": report.nightopen_count, "status": "양호" if report.nightopen_count else "주의"},
            {"name": "응급 시설", "value": report.emeropen_count, "status": "양호" if report.emeropen_count else "주의"},
        ],
        "map": report.medic_map,
        "data_source": "PUBLIC_DATA",
    }
