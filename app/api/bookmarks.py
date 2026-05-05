# 불완전: 저장/해제/목록 라우터는 구현됐지만 실제 DB 연결 후 unique constraint와 paging 통합 검증이 필요함.
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.bookmark import CreateBookmarkRequest
from app.schemas.common import success_response
from app.services import bookmark_service

router = APIRouter(prefix="/bookmarks", tags=["bookmarks"])


@router.get("/properties")
async def list_bookmarks(
    status: str = Query(default="ALL"),
    page: int = Query(default=1),
    size: int = Query(default=10, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return success_response(await bookmark_service.list_bookmarks(db, current_user, status, page, size))


@router.post("/properties")
async def create_bookmark(
    request: CreateBookmarkRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return success_response(
        await bookmark_service.create_bookmark(db, current_user, request.property_id, request.report_id),
        status_code=201,
    )


@router.delete("/properties/{id}")
async def delete_bookmark(
    id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return success_response(await bookmark_service.delete_bookmark(db, current_user, id))
