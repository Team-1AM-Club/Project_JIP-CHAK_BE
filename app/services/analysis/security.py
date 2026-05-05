# 불완전: 치안 점수 계산 구조는 구현됐지만 실제 범죄/CCTV/가로등 데이터 기준 산식 검증이 필요함.
from app.models.report import Report
from app.services.analysis.scorer import summary_for_score


def calculate_security_score(report: Report) -> int:
    if report.security_score is not None:
        return report.security_score
    crimes = sum(report.criminal_occur or [])
    score = 70
    score += min(report.cctv_count, 20)
    score += min(report.lamp_count // 5, 10)
    score -= min(crimes // 10, 35)
    score -= 10 if report.police_dist > 1500 else 0
    return max(0, min(100, score))


def get_security_detail(report: Report) -> dict:
    score = calculate_security_score(report)
    return {
        "score": score,
        "base_score": score,
        "summary": summary_for_score(score),
        "indicators": [
            {"name": "CCTV 수", "value": report.cctv_count, "status": "양호" if report.cctv_count >= 10 else "주의"},
            {"name": "가로등 수", "value": report.lamp_count, "status": "양호" if report.lamp_count >= 30 else "주의"},
            {"name": "경찰서 거리", "value": report.police_dist, "status": "주의" if report.police_dist > 1500 else "양호"},
        ],
        "map": report.safety_map,
        "data_source": "PUBLIC_DATA",
    }
