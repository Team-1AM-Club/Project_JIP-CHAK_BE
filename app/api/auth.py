# 불완전: 라우터 흐름은 구현됐지만 실제 Google OAuth 연동 전까지는 mock login에 의존함.
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import LoginRequest, LogoutRequest, ReissueRequest
from app.schemas.common import success_response
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login")
async def login(request: LoginRequest, db: AsyncSession = Depends(get_db)):
    data = await auth_service.social_login(db, request.provider, request.code, request.redirect_uri)
    return success_response(data)


@router.post("/reissue")
async def reissue(request: ReissueRequest, db: AsyncSession = Depends(get_db)):
    return success_response(await auth_service.reissue_tokens(db, request.refresh_token))


@router.post("/logout")
async def logout(
    request: LogoutRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return success_response(await auth_service.logout(db, request.refresh_token))
