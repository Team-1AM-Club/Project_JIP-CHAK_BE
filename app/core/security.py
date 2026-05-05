# 완벽: JWT 생성/검증, 만료 처리, refresh token hash 유틸은 독립 로직으로 구현되어 앱 import 검증까지 완료됨.
import hashlib
from datetime import datetime, timedelta, timezone
from uuid import UUID

from jose import ExpiredSignatureError, JWTError, jwt

from app.core.config import settings
from app.core.exceptions import ExpiredTokenError, InvalidTokenError


def create_access_token(user_id: UUID) -> str:
    return _create_token(user_id=user_id, token_type="access", expires_in=settings.ACCESS_TOKEN_EXPIRE)


def create_refresh_token(user_id: UUID) -> str:
    return _create_token(user_id=user_id, token_type="refresh", expires_in=settings.REFRESH_TOKEN_EXPIRE)


def decode_token(token: str, expected_type: str | None = None) -> dict:
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
    except ExpiredSignatureError as exc:
        raise ExpiredTokenError() from exc
    except JWTError as exc:
        raise InvalidTokenError() from exc

    token_type = payload.get("type")
    if expected_type is not None and token_type != expected_type:
        raise InvalidTokenError()
    if not payload.get("sub"):
        raise InvalidTokenError()
    return payload


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def verify_token_hash(token: str, hashed: str) -> bool:
    return hash_token(token) == hashed


def _create_token(user_id: UUID, token_type: str, expires_in: int) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "type": token_type,
        "iat": now,
        "exp": now + timedelta(seconds=expires_in),
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
