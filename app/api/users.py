# 불완전: 라우터와 서비스 연결은 완료됐지만 실제 DB 세션으로 조회/수정하는 통합 테스트가 필요함.
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.common import success_response
from app.schemas.user import UpdateProfileRequest, UpdateSettingsRequest, UpdateWeightsRequest
from app.services import user_service

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/myprofile")
async def get_my_profile(current_user: User = Depends(get_current_user)):
    return success_response(user_service.profile_response(current_user))


@router.patch("/myprofile")
async def update_my_profile(
    request: UpdateProfileRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return success_response(await user_service.update_profile(db, current_user, request.user_type_id))


@router.get("/settings")
async def get_settings(current_user: User = Depends(get_current_user)):
    return success_response(user_service.settings_response(current_user))


@router.patch("/settings")
async def update_settings(
    request: UpdateSettingsRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    data = await user_service.update_settings(
        db,
        current_user,
        request.noti_enabled,
        request.dark_mode,
    )
    return success_response(data)


@router.patch("/weights")
async def update_weights(
    request: UpdateWeightsRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return success_response(await user_service.update_weights(db, current_user, request.model_dump()))


@router.delete("/me")
async def withdraw(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return success_response(await user_service.withdraw(db, current_user))
