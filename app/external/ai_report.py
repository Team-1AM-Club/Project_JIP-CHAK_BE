import logging
from openai import AsyncOpenAI

from app.core.config import settings

logger = logging.getLogger(__name__)

_client: AsyncOpenAI | None = None

MODEL = "solar-pro3"
MAX_TOKENS = 100
TEMPERATURE = 0.6
TIMEOUT = 10.0

SYSTEM_PROMPT = (
    "역할: 서울시 데이터 기반 주거 환경 분석 전문가\n"
    "미션: 5대 리스크 점수를 해석하여 주거지 특징과 실거주 팁을 담은 한 줄 요약을 생성\n"
    "제약 조건:\n"
    "- 한 문장(공백 포함 50자 이내)으로 작성, 존댓말 사용, 이모지 사용 금지\n"
    "- 주소, 개별 점수, 등급 등 화면에 이미 노출된 중복 정보 언급 금지\n"
    "- 거주자에게 실질적 인사이트 및 필요한 행동 조언 전달\n"
    "- '거주 적합도', '등급' 등 상하 위계를 나누는 단어 대신 '일상의 쾌적함', '균형 잡힌 환경', '보완이 필요한 입지' 등 자연스러운 표현을 사용\n"
    "- 전문 용어 대신 일상적 언어를 사용하되 품격을 유지"
)


def _get_client() -> AsyncOpenAI | None:
    global _client
    if settings.UPSTAGE_AI_API_KEY is None:
        return None
    if _client is None:
        _client = AsyncOpenAI(
            api_key=settings.UPSTAGE_AI_API_KEY,
            base_url="https://api.upstage.ai/v1",
            timeout=TIMEOUT,
        )
    return _client


async def generate_overall_summary(
    address: str,
    total_score: int,
    grade: str,
    categories: list[dict],
) -> str | None:
    """종합 리포트 AI 한 줄 요약 생성.

    categories 예시: [{"title": "치안 리스크", "score": 68, "grade": "양호"}, ...]
    AI 호출 실패 또는 API 키 미설정 시 None 반환 → 호출측에서 Fallback 처리.
    """
    client = _get_client()
    if client is None:
        return None

    category_lines = "\n".join(
        f"- {c['title']}: {c['score']}점 ({c['grade']})" for c in categories
    )
    user_prompt = (
        f"[종합 리포트 요약 요청]\n"
        f"주소: {address}\n"
        f"종합 점수: {total_score}점 (등급: {grade})\n\n"
        f"카테고리별 점수:\n{category_lines}\n\n"
        f"위 데이터를 바탕으로 이 지역의 전반적 거주 적합성을 한 줄로 요약해주세요."
    )

    try:
        response = await client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=MAX_TOKENS,
            temperature=TEMPERATURE,
        )
        return response.choices[0].message.content.strip()
    except Exception:
        logger.warning("AI 종합 요약 생성 실패: address=%s", address, exc_info=True)
        return None


async def generate_category_summary(
    address: str,
    category_title: str,
    score: int,
    grade: str,
    indicators: list[dict],
) -> str | None:
    """카테고리별 상세 리포트 AI 한 줄 요약 생성.

    indicators 예시: [{"name": "범죄 발생", "display_value": "3,000건", "score": 55, "status": "주의"}, ...]
    AI 호출 실패 또는 API 키 미설정 시 None 반환.
    """
    client = _get_client()
    if client is None:
        return None

    indicator_lines = "\n".join(
        f"- {ind['name']}: {ind.get('display_value', ind.get('raw_value', '?'))} → "
        f"{ind['score']}점 ({ind.get('status', '분석중')})"
        if ind.get("score") is not None
        else f"- {ind['name']}: 데이터 없음"
        for ind in indicators
    )
    user_prompt = (
        f"[{category_title} 상세 분석 요약 요청]\n"
        f"주소: {address}\n"
        f"카테고리 점수: {score}점 (등급: {grade})\n\n"
        f"세부 지표:\n{indicator_lines}\n\n"
        f"위 세부 지표 데이터를 바탕으로 이 지역의 {category_title} 상황을 한 줄로 요약해주세요."
    )

    try:
        response = await client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=MAX_TOKENS,
            temperature=TEMPERATURE,
        )
        return response.choices[0].message.content.strip()
    except Exception:
        logger.warning("AI 카테고리 요약 생성 실패: %s", category_title, exc_info=True)
        return None


COMPARE_SYSTEM_PROMPT = (
    "역할: 서울시 주거 환경 데이터 기반 입지 비교 전문가\n"
    "미션: 두 후보지의 5대 리스크 점수를 비교하여 어느 곳이 왜 더 적합한지를 담은 한 줄 추천 문장 생성\n"
    "제약 조건:\n"
    "- 한 문장(공백 포함 60자 이내)으로 작성, 존댓말 사용, 이모지 사용 금지\n"
    "- 주소, 개별 점수, 등급 등 화면에 이미 노출된 중복 정보 언급 금지\n"
    "- 두 지역 간 차이를 근거로 추천 이유를 명확히 전달\n"
    "- '더 좋다', '추천드립니다' 등 단순 비교 대신 구체적 생활 맥락을 담아 표현\n"
    "- 전문 용어 대신 일상적 언어를 사용하되 품격을 유지"
)


async def generate_comparison_recommendation(
    address_a: str,
    address_b: str,
    scores_a: dict[str, int],
    scores_b: dict[str, int],
    total_a: int,
    total_b: int,
    recommended_address: str,
) -> str | None:
    """1:1 비교 기반 추천 한 줄 요약 생성.

    scores_a/b 예시: {"flood": 82, "security": 71, "medical": 88, "noise": 58, "congestion": 64}
    AI 호출 실패 또는 API 키 미설정 시 None 반환 → 호출측에서 Fallback 처리.
    """
    client = _get_client()
    if client is None:
        return None

    category_labels = {
        "flood": "침수", "security": "야간 치안", "medical": "의료", "noise": "소음", "congestion": "혼잡",
    }
    diff_lines = "\n".join(
        f"- {category_labels.get(cat, cat)}: {address_a} {scores_a.get(cat, 0)}점 vs {address_b} {scores_b.get(cat, 0)}점"
        for cat in category_labels
    )
    user_prompt = (
        f"[1:1 입지 비교 추천 요청]\n"
        f"후보지 A: {address_a} (종합 {total_a}점)\n"
        f"후보지 B: {address_b} (종합 {total_b}점)\n\n"
        f"카테고리별 비교:\n{diff_lines}\n\n"
        f"추천 후보지: {recommended_address}\n\n"
        f"위 데이터를 바탕으로 {recommended_address}를 추천하는 이유를 한 줄로 설명해주세요."
    )

    try:
        response = await client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": COMPARE_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=MAX_TOKENS,
            temperature=TEMPERATURE,
        )
        return response.choices[0].message.content.strip()
    except Exception:
        logger.warning("AI 비교 추천 생성 실패: %s vs %s", address_a, address_b, exc_info=True)
        return None