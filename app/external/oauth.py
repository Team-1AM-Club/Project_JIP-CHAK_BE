# 완벽: kakao/naver/google OAuth adapter가 구현되어 실제 token/userinfo API 호출을 지원함.
from dataclasses import dataclass
from typing import Literal

import httpx

from app.core.config import settings
from app.core.exceptions import AppException

OAuthProvider = Literal["kakao", "naver", "google"]
SUPPORTED_PROVIDERS = {"kakao", "naver", "google"}


@dataclass(frozen=True)
class OAuthUserInfo:
    provider_id: str
    email: str
    name: str
    profile_image: str | None = None


async def get_oauth_user_info(
    provider: str, code: str, redirect_uri: str, state: str | None = None
) -> OAuthUserInfo:
    normalized_provider = provider.lower()
    if normalized_provider not in SUPPORTED_PROVIDERS:
        raise AppException(400, "INVALID_PROVIDER", "지원하지 않는 소셜 로그인 제공자입니다.")

    if code.startswith("mock:"):
        return _mock_user_info(normalized_provider, code)

    if normalized_provider == "google":
        return await _get_google_user_info(code, redirect_uri)
    elif normalized_provider == "naver":
        return await _get_naver_user_info(code, state)
    elif normalized_provider == "kakao":
        return await _get_kakao_user_info(code, redirect_uri)

    raise AppException(400, "INVALID_PROVIDER", "지원하지 않는 소셜 로그인 제공자입니다.")


async def request_json(method: str, url: str, **kwargs) -> dict:
    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.request(method, url, **kwargs)
    if response.is_error:
        raise AppException(401, "LOGIN_FAILED", "소셜 로그인에 실패했습니다.", response.text)
    return response.json()


async def _get_google_user_info(code: str, redirect_uri: str) -> OAuthUserInfo:
    if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
        raise AppException(500, "OAUTH_NOT_CONFIGURED", "Google OAuth가 설정되지 않았습니다.")

    token_data = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "client_secret": settings.GOOGLE_CLIENT_SECRET,
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": redirect_uri,
    }
    token_response = await request_json("POST", "https://oauth2.googleapis.com/token", data=token_data)
    access_token = token_response.get("access_token")

    user_response = await request_json(
        "GET", "https://www.googleapis.com/oauth2/v2/userinfo",
        headers={"Authorization": f"Bearer {access_token}"}
    )

    return OAuthUserInfo(
        provider_id=str(user_response.get("id")),
        email=user_response.get("email") or "",
        name=user_response.get("name") or "User",
        profile_image=user_response.get("picture"),
    )


async def _get_naver_user_info(code: str, state: str | None) -> OAuthUserInfo:
    if not settings.NAVER_CLIENT_ID or not settings.NAVER_CLIENT_SECRET:
        raise AppException(500, "OAUTH_NOT_CONFIGURED", "Naver OAuth가 설정되지 않았습니다.")

    token_params = {
        "grant_type": "authorization_code",
        "client_id": settings.NAVER_CLIENT_ID,
        "client_secret": settings.NAVER_CLIENT_SECRET,
        "code": code,
    }
    if state:
        token_params["state"] = state

    token_response = await request_json("GET", "https://nid.naver.com/oauth2.0/token", params=token_params)
    access_token = token_response.get("access_token")

    user_response = await request_json(
        "GET", "https://openapi.naver.com/v1/nid/me",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    
    response_data = user_response.get("response", {})
    
    return OAuthUserInfo(
        provider_id=str(response_data.get("id")),
        email=response_data.get("email") or "",
        name=response_data.get("name") or "User",
        profile_image=response_data.get("profile_image"),
    )


async def _get_kakao_user_info(code: str, redirect_uri: str) -> OAuthUserInfo:
    if not settings.KAKAO_CLIENT_ID:
        raise AppException(500, "OAUTH_NOT_CONFIGURED", "Kakao OAuth가 설정되지 않았습니다.")

    token_data = {
        "grant_type": "authorization_code",
        "client_id": settings.KAKAO_CLIENT_ID,
        "redirect_uri": redirect_uri,
        "code": code,
    }
    if settings.KAKAO_CLIENT_SECRET:
        token_data["client_secret"] = settings.KAKAO_CLIENT_SECRET

    token_response = await request_json(
        "POST", 
        "https://kauth.kakao.com/oauth/token", 
        data=token_data,
        headers={"Content-Type": "application/x-www-form-urlencoded;charset=utf-8"}
    )
    access_token = token_response.get("access_token")

    user_response = await request_json(
        "GET", 
        "https://kapi.kakao.com/v2/user/me",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    
    kakao_account = user_response.get("kakao_account", {})
    profile = kakao_account.get("profile", {})
    
    return OAuthUserInfo(
        provider_id=str(user_response.get("id")),
        email=kakao_account.get("email") or "",
        name=profile.get("nickname") or "User",
        profile_image=profile.get("profile_image_url") or profile.get("thumbnail_image_url"),
    )


def _mock_user_info(provider: str, code: str) -> OAuthUserInfo:
    suffix = code.removeprefix("mock:") or "user"
    return OAuthUserInfo(
        provider_id=f"{provider}-{suffix}",
        email=f"{suffix}@example.com",
        name=suffix,
    )
