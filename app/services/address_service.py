# 불완전: 입력 검증은 구현됐지만 실제 행안부 Geocoding client 연동과 응답 파싱 검증이 필요함.
from app.core.exceptions import AppException
from app.external import geocoding


async def search(query: str, page: int, size: int) -> dict:
    if len(query.strip()) < 2:
        raise AppException(400, "INVALID_QUERY", "검색어는 2자 이상 입력해 주세요.")
    if page < 1 or size < 1 or size > 20:
        raise AppException(400, "INVALID_INPUT_VALUE", "페이지 값이 올바르지 않습니다.")

    result = await geocoding.search_address(query, page, size)
    total_count = result["total_count"]
    return {
        "query": query,
        "total_count": total_count,
        "current_page": page,
        "total_pages": (total_count + size - 1) // size if total_count else 0,
        "results": result["results"],
    }


async def map_search(lat: float, lng: float) -> dict:
    if lat < -90 or lat > 90:
        raise AppException(400, "INVALID_COORDINATES", "유효하지 않은 좌표입니다.", "Latitude must be between -90 and 90")
    if lng < -180 or lng > 180:
        raise AppException(400, "INVALID_COORDINATES", "유효하지 않은 좌표입니다.", "Longitude must be between -180 and 180")
    return await geocoding.reverse_geocode(lat, lng)
