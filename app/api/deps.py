# 불완전: Bearer token 파싱/사용자 조회 로직은 구현됐지만 실제 DB 연결 상태에서의 사용자 조회 테스트가 필요함.
from uuid import UUID

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import InvalidTokenError, UnauthorizedError, UserNotFoundError
from app.core.security import decode_token
from app.db.session import get_db
from app.models.user import User

bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    if credentials is None:
        raise UnauthorizedError()

    if credentials.scheme.lower() != "bearer" or not credentials.credentials:
        raise InvalidTokenError()

    payload = decode_token(credentials.credentials, expected_type="access")
    try:
        user_id = UUID(payload["sub"])
    except (KeyError, ValueError) as exc:
        raise InvalidTokenError() from exc

    user = await db.scalar(select(User).where(User.user_id == user_id))
    if user is None:
        raise UserNotFoundError()
    return user
