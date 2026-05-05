# 완벽: 사용자 유형 프리셋, 등급 변환, 점수 상태 변환은 외부 의존 없는 순수 상수/함수로 구현됨.
USER_TYPE_PRESETS = {
    "Single": {
        "user_type_id": 1,
        "user_type_name": "청년 1인 가구",
        "user_type_desc": "안전·소음·침수 가중치 적용 우선",
        "preset_weights": {
            "security": 35,
            "noise": 30,
            "medical": 5,
            "flood": 25,
            "congestion": 5,
        },
    },
    "Newlyweds": {
        "user_type_id": 2,
        "user_type_name": "신혼 / 예비 부부",
        "user_type_desc": "소음·혼잡·의료 가중치 적용",
        "preset_weights": {
            "medical": 25,
            "security": 5,
            "congestion": 30,
            "noise": 35,
            "flood": 5,
        },
    },
    "Dependents": {
        "user_type_id": 3,
        "user_type_name": "부모 동거 가구",
        "user_type_desc": "의료·치안·침수 가중치 적용",
        "preset_weights": {
            "medical": 45,
            "security": 10,
            "noise": 5,
            "flood": 35,
            "congestion": 5,
        },
    },
}


REPORT_CATEGORIES = {
    "flood": {"title": "침수 리스크", "icon": "water"},
    "security": {"title": "치안 리스크", "icon": "moon"},
    "medical": {"title": "의료 접근성", "icon": "medical"},
    "noise": {"title": "소음 리스크", "icon": "sound"},
    "congestion": {"title": "혼잡 리스크", "icon": "people"},
}


def user_type_by_id(user_type_id: int) -> str | None:
    for user_type, preset in USER_TYPE_PRESETS.items():
        if preset["user_type_id"] == user_type_id:
            return user_type
    return None


def grade_from_score(score: int | None) -> str:
    if score is None:
        return "분석중"
    if score >= 80:
        return "안심"
    if score >= 60:
        return "양호"
    if score >= 40:
        return "주의"
    return "위험"


def score_status(score: int | None) -> str:
    if score is None:
        return "RISK"
    if score >= 80:
        return "SAFE"
    if score >= 60:
        return "CAUTION"
    return "RISK"
