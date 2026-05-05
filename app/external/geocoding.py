# 불완전: Geocoding adapter 형태만 마련했고 실제 행안부 주소 검색/Reverse Geocoding 호출은 아직 placeholder임.
from app.core.exceptions import AppException


async def search_address(query: str, page: int, size: int) -> dict:
    if "서울" not in query:
        return {"total_count": 0, "results": []}
    return {
        "total_count": 1,
        "results": [
            {
                "road_addr": query,
                "jibun_addr": query,
                "zip_code": None,
                "sido": "서울특별시",
                "sigungu": _find_gu(query),
                "dong": _find_dong(query),
                "dong_code": None,
                "lat": None,
                "lng": None,
                "is_service_area": True,
            }
        ],
    }


async def reverse_geocode(lat: float, lng: float) -> dict:
    if not (33.0 <= lat <= 39.5 and 124.0 <= lng <= 132.0):
        raise AppException(404, "ADDRESS_NOT_FOUND", "해당 위치의 주소를 찾을 수 없습니다.")
    return {
        "lat": lat,
        "lng": lng,
        "road_addr": "서울특별시 주소 확인 필요",
        "road_addr_eng": None,
        "jibun_addr": "서울특별시 주소 확인 필요",
        "zip_code": None,
        "sido": "서울특별시",
        "sigungu": None,
        "dong": None,
        "dong_code": None,
        "is_service_area": True,
        "building_name": None,
        "distance": 0,
    }


def _find_gu(address: str) -> str | None:
    return next((part for part in address.split() if part.endswith("구")), None)


def _find_dong(address: str) -> str | None:
    return next((part for part in address.split() if part.endswith("동")), None)
