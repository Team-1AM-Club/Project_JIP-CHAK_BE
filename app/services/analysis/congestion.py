# 불완전: 혼잡 점수 계산 구조는 구현됐지만 실제 생활인구/교통 데이터 기준 산식 검증이 필요함.
from app.models.report import Report
from app.services.analysis.scorer import summary_for_score


def calculate_congestion_score(report: Report) -> int:
    if report.congestion_score is not None:
        return report.congestion_score
    data = report.congestion_data or {}
    peak_index = int(data.get("peak_index", 50))
    return max(0, min(100, 100 - peak_index))


def get_congestion_detail(report: Report) -> dict:
    score = calculate_congestion_score(report)
    return {
        "score": score,
        "base_score": score,
        "summary": summary_for_score(score),
        "indicators": [
            {"name": "피크 혼잡도", "value": (report.congestion_data or {}).get("peak_index", 50), "status": "주의" if score < 60 else "양호"},
        ],
        "chart": report.congestion_data,
        "data_source": "PUBLIC_DATA",
    }
