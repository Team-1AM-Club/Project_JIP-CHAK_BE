# 불완전: API contract는 구현됐지만 주소 검색/지도 검색은 실제 행안부 Geocoding 연동 전 placeholder를 사용함.
from fastapi import APIRouter, Depends, Query

from app.api.deps import get_current_user
from app.models.user import User
from app.schemas.common import success_response
from app.services import address_service

router = APIRouter(prefix="/addresses", tags=["addresses"])


@router.get("/search")
async def search_address(
    query: str,
    page: int = Query(default=1),
    size: int = Query(default=10, le=20),
    current_user: User = Depends(get_current_user),
):
    return success_response(await address_service.search(query, page, size))


@router.get("/map-search")
async def map_search(
    lat: float,
    lng: float,
    current_user: User = Depends(get_current_user),
):
    return success_response(await address_service.map_search(lat, lng))

