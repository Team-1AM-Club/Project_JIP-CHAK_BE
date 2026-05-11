# 불완전: 정규화/가중합 유틸은 준비됐지만 p05/p95 기준값은 DB 전처리 테이블 확정 후 주입되어야 함.
from app.core.constants import grade_from_score


def clamp_score(value: float | int | None) -> int:
    if value is None:
        return 0
    return max(0, min(100, round(value)))


def normalize(value: float | int | None, p05: float, p95: float, *, inverse: bool = False) -> int:
    if value is None or p95 == p05:
        return 0
    score = (float(value) - p05) / (p95 - p05) * 100
    if inverse:
        score = 100 - score
    return clamp_score(score)


def weighted_sum(items: list[tuple[int, float]]) -> int:
    if not items:
        return 0
    total_weight = sum(weight for _, weight in items)
    if total_weight <= 0:
        return 0
    return clamp_score(sum(score * weight for score, weight in items) / total_weight)


def calculate_total_score(category_scores: dict[str, int | None], weights: dict[str, int]) -> int:
    total = 0.0
    for category, weight in weights.items():
        score = category_scores.get(category)
        total += (score or 0) * (weight / 100)
    return clamp_score(total)


def summary_for_score(score: int | None) -> str:
    grade = grade_from_score(score)
    if grade == "안심":
        return "전반적으로 안정적인 생활 환경입니다."
    if grade == "양호":
        return "대체로 양호하지만 일부 항목은 확인이 필요합니다."
    if grade == "주의":
        return "생활 리스크가 있어 현장 확인을 권장합니다."
    if grade == "위험":
        return "주요 생활 리스크가 높아 신중한 검토가 필요합니다."
    return "분석이 아직 완료되지 않았습니다."
