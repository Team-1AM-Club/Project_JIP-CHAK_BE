# 불완전: Google OAuth adapter 형태만 마련했고 실제 token/userinfo API 호출은 아직 mock 경로로 대체됨.
from dataclasses import dataclass

import httpx

from app.core.exceptions import AppException


@dataclass(frozen=True)
class OAuthUserInfo:
    provider_id: str
    email: str
    name: str
    profile_image: str | None = None


async def get_oauth_user_info(provider: str, code: str, redirect_uri: str) -> OAuthUserInfo:
    normalized_provider = provider.lower()
    if normalized_provider != "google":
        raise AppException(400, "INVALID_PROVIDER", "Google 로그인만 지원합니다.")

    if code.startswith("mock:"):
        suffix = code.removeprefix("mock:") or "user"
        return OAuthUserInfo(
            provider_id=f"{normalized_provider}-{suffix}",
            email=f"{suffix}@example.com",
            name=suffix,
        )

    raise AppException(
        401,
        "LOGIN_FAILED",
        "소셜 로그인에 실패했습니다.",
        "OAuth provider 연동 정보가 아직 설정되지 않았습니다. 테스트는 code='mock:{name}' 형식을 사용하세요.",
    )


async def request_json(method: str, url: str, **kwargs) -> dict:
    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.request(method, url, **kwargs)
    if response.is_error:
        raise AppException(401, "LOGIN_FAILED", "소셜 로그인에 실패했습니다.", response.text)
    return response.json()
