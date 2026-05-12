# 불완전: JWT/RTR 흐름은 구현됐지만 실제 Google OAuth 연동과 DB 기반 refresh token 재사용 테스트가 필요함.
from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import AppException
from app.core.security import create_access_token, create_refresh_token, decode_token, hash_token
from app.external.oauth import get_oauth_user_info
from app.models.refresh_token import RefreshToken
from app.models.user import User
from app.services.user_service import is_customized


async def social_login(db: AsyncSession, provider: str, code: str, redirect_uri: str, state: str | None = None) -> dict:
    provider = provider.lower()
    user_info = await get_oauth_user_info(provider, code, redirect_uri, state)

    user = await db.scalar(
        select(User).where(User.provider == provider.upper(), User.provider_id == user_info.provider_id)
    )
    is_new_user = user is None
    if user is None:
        email = user_info.email
        if not email:
            email = f"{user_info.provider_id}@{provider.lower()}.dummy.com"

        # 이메일 중복 체크 (다른 소셜로 이미 가입된 경우)
        existing_user = await db.scalar(select(User).where(User.email == email))
        if existing_user:
            raise AppException(
                400,
                "EMAIL_ALREADY_EXISTS",
                f"해당 이메일은 이미 {existing_user.provider} 계정으로 가입되어 있습니다."
            )

        user = User(
            user_name=user_info.name,
            email=email,
            provider=provider.upper(),
            provider_id=user_info.provider_id,
        )
        db.add(user)
        await db.flush()

    tokens = await issue_tokens(db, user)
    await db.commit()
    await db.refresh(user)

    return {
        "is_new_user": is_new_user,
        "user": _login_user_response(user, user_info.profile_image),
        **tokens,
    }


async def reissue_tokens(db: AsyncSession, refresh_token: str) -> dict:
    payload = decode_token(refresh_token, expected_type="refresh")
    token_hash = hash_token(refresh_token)
    stored_token = await db.scalar(select(RefreshToken).where(RefreshToken.token_hash == token_hash))

    if stored_token is None:
        user_id = payload.get("sub")
        if user_id:
            await db.execute(delete(RefreshToken).where(RefreshToken.user_id == UUID(user_id)))
            await db.commit()
        raise AppException(401, "REFRESH_TOKEN_REUSED", "Refresh Token이 재사용되었습니다.")

    now = datetime.now(timezone.utc)
    if stored_token.expires_at < now:
        await db.delete(stored_token)
        await db.commit()
        raise AppException(401, "EXPIRED_TOKEN", "토큰이 만료되었습니다.")

    user = await db.get(User, stored_token.user_id)
    if user is None:
        raise AppException(404, "USER_NOT_FOUND", "사용자를 찾을 수 없습니다.")

    await db.delete(stored_token)
    tokens = await issue_tokens(db, user)
    await db.commit()
    return tokens


async def logout(db: AsyncSession, refresh_token: str) -> dict:
    await db.execute(delete(RefreshToken).where(RefreshToken.token_hash == hash_token(refresh_token)))
    await db.commit()
    return {"message": "로그아웃되었습니다."}


async def issue_tokens(db: AsyncSession, user: User) -> dict:
    access_token = create_access_token(user.user_id)
    refresh_token = create_refresh_token(user.user_id)
    db.add(
        RefreshToken(
            user_id=user.user_id,
            token_hash=hash_token(refresh_token),
            expires_at=datetime.now(timezone.utc) + timedelta(seconds=settings.REFRESH_TOKEN_EXPIRE),
        )
    )
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "expires_in": settings.ACCESS_TOKEN_EXPIRE,
        "refresh_expires_in": settings.REFRESH_TOKEN_EXPIRE,
    }


def _login_user_response(user: User, profile_image: str | None) -> dict:
    return {
        "id": user.user_id,
        "name": user.user_name,
        "email": user.email,
        "profile_image": profile_image,
        "provider": user.provider.lower(),
        "created_at": user.created_at,
        "has_preferences": is_customized(user),
        "subscription": {"plan": "FREE", "expires_at": None},
    }
