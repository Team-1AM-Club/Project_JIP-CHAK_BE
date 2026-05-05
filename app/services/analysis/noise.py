# 불완전: 소음 점수 계산 구조는 구현됐지만 실제 도로소음/민원/철도소음 기준 산식 검증이 필요함.
from app.models.report import Report
from app.services.analysis.scorer import summary_for_score


def calculate_noise_score(report: Report) -> int:
    if report.noise_score is not None:
        return report.noise_score
    score = 100
    score -= min(max(report.road_noise - 45, 0), 30)
    score -= min(report.noise_report, 20)
    score -= min(report.ent_place, 20)
    score -= 10 if report.train_noise else 0
    return max(0, min(100, score))


def get_noise_detail(report: Report) -> dict:
    score = calculate_noise_score(report)
    return {
        "score": score,
        "base_score": score,
        "summary": summary_for_score(score),
        "indicators": [
            {"name": "도로 소음", "value": report.road_noise, "status": "주의" if report.road_noise >= 65 else "양호"},
            {"name": "소음 민원", "value": report.noise_report, "status": "주의" if report.noise_report else "양호"},
            {"name": "유흥업소", "value": report.ent_place, "status": "주의" if report.ent_place >= 5 else "양호"},
        ],
        "chart": report.noise_table,
        "data_source": "PUBLIC_DATA",
    }
