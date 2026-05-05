# 불완전: 침수 점수 계산 구조는 구현됐지만 실제 공공데이터 지표별 산식 확정 후 보정이 필요함.
from app.models.report import Report
from app.services.analysis.scorer import summary_for_score


def calculate_flood_score(report: Report) -> int:
    if report.flood_score is not None:
        return report.flood_score
    score = 100
    score -= min(report.flood_hist * 12, 40)
    score -= min(report.low_ratio, 25)
    score += min(report.pump_cap // 5, 10)
    score -= 15 if report.river_dist < 300 else 0
    return max(0, min(100, score))


def get_flood_detail(report: Report) -> dict:
    score = calculate_flood_score(report)
    return {
        "score": score,
        "base_score": score,
        "summary": summary_for_score(score),
        "indicators": [
            {"name": "침수 이력", "value": report.flood_hist, "status": "주의" if report.flood_hist else "양호"},
            {"name": "저지대 비율", "value": report.low_ratio, "status": "주의" if report.low_ratio >= 30 else "양호"},
            {"name": "하천 거리", "value": report.river_dist, "status": "주의" if report.river_dist < 300 else "양호"},
        ],
        "map": report.flood_map,
        "data_source": "PUBLIC_DATA",
    }
