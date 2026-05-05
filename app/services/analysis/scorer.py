# 완벽: 카테고리 점수와 사용자 가중치로 종합 점수를 계산하는 순수 함수는 완결된 형태임.
from app.core.constants import grade_from_score


def calculate_total_score(category_scores: dict[str, int | None], weights: dict[str, int]) -> int:
    total = 0.0
    for category, weight in weights.items():
        score = category_scores.get(category)
        total += (score or 0) * (weight / 100)
    return max(0, min(100, round(total)))


def summary_for_score(score: int | None) -> str:
    grade = grade_from_score(score)
    if grade == "안심":
        return "전반적으로 안정적인 생활 환경입니다."
    if grade == "양호":
        return "대체로 양호하지만 일부 항목은 확인이 필요합니다."
    if grade == "주의":
        return "생활 리스크가 있어 세부 항목 확인을 권장합니다."
    if grade == "위험":
        return "주요 생활 리스크가 높아 신중한 검토가 필요합니다."
    return "분석이 아직 완료되지 않았습니다."
