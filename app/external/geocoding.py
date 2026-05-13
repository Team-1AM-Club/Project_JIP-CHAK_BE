
from typing import Protocol

import httpx

from app.core.config import settings
from app.core.exceptions import AppException

NAVER_GEOCODE_URL = "https://maps.apigw.ntruss.com/map-geocode/v2/geocode"
NAVER_REVERSE_GEOCODE_URL = "https://maps.apigw.ntruss.com/map-reversegeocode/v2/gc"
REQUEST_TIMEOUT = 5.0


class GeocodingClient(Protocol):
    async def search_address(self, query: str, page: int, size: int) -> dict:
        ...

    async def reverse_geocode(self, lat: float, lng: float) -> dict:
        ...


class MockGeocodingClient:
    async def search_address(self, query: str, page: int, size: int) -> dict:
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

    async def reverse_geocode(self, lat: float, lng: float) -> dict:
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


class NaverGeocodingClient:
    async def search_address(self, query: str, page: int, size: int) -> dict:
        payload = await self._get(
            NAVER_GEOCODE_URL,
            {
                "query": query,
                "page": page,
                "count": size,
            },
        )
        addresses = payload.get("addresses", [])
        return {
            "total_count": int(payload.get("meta", {}).get("totalCount") or len(addresses)),
            "results": [_naver_address_result(item) for item in addresses],
        }

    async def reverse_geocode(self, lat: float, lng: float) -> dict:
        payload = await self._get(
            NAVER_REVERSE_GEOCODE_URL,
            {
                "coords": f"{lng},{lat}",
                "orders": "roadaddr,addr,admcode",
                "output": "json",
            },
        )
        results = payload.get("results", [])
        if not results:
            raise AppException(404, "ADDRESS_NOT_FOUND", "해당 위치의 주소를 찾을 수 없습니다.")
        return _naver_reverse_result(lat, lng, results)

    async def _get(self, url: str, params: dict) -> dict:
        if not settings.NAVER_MAPS_CLIENT_ID or not settings.NAVER_MAPS_CLIENT_SECRET:
            raise AppException(
                500,
                "GEOCODING_CONFIG_MISSING",
                "Naver Maps API 설정이 필요합니다.",
            )
        headers = {
            "X-NCP-APIGW-API-KEY-ID": settings.NAVER_MAPS_CLIENT_ID,
            "X-NCP-APIGW-API-KEY": settings.NAVER_MAPS_CLIENT_SECRET,
        }
        try:
            async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
                response = await client.get(url, params=params, headers=headers)
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as exc:
            raise AppException(
                502,
                "GEOCODING_API_ERROR",
                "Naver Geocoding API 호출에 실패했습니다.",
                {"status_code": exc.response.status_code, "body": exc.response.text},
            ) from exc
        except httpx.HTTPError as exc:
            raise AppException(
                502,
                "GEOCODING_API_ERROR",
                "Naver Geocoding API 호출 중 네트워크 오류가 발생했습니다.",
                str(exc),
            ) from exc


_GU_NAME_TO_CODE: dict[str, str] = {
    "종로구": "11110", "중구": "11140", "용산구": "11170",
    "성동구": "11200", "광진구": "11215", "동대문구": "11230",
    "중랑구": "11260", "성북구": "11290", "강북구": "11305",
    "도봉구": "11320", "노원구": "11350", "은평구": "11380",
    "서대문구": "11410", "마포구": "11440", "양천구": "11470",
    "강서구": "11500", "구로구": "11530", "금천구": "11545",
    "영등포구": "11560", "동작구": "11590", "관악구": "11620",
    "서초구": "11650", "강남구": "11680", "송파구": "11710",
    "강동구": "11740",
}


def _gu_code_from_sigungu(sigungu: str | None) -> str | None:
    if not sigungu:
        return None
    return _GU_NAME_TO_CODE.get(sigungu)


def _naver_address_result(item: dict) -> dict:
    elements = item.get("addressElements") or []
    sido = _find_element(elements, "SIDO")
    sigungu = _find_element(elements, "SIGUGUN")
    dong = _find_element(elements, "DONGMYUN") or _find_element(elements, "LEGALDONG")
    lat = _to_float(item.get("y"))
    lng = _to_float(item.get("x"))
    return {
        "road_addr": item.get("roadAddress") or item.get("jibunAddress"),
        "jibun_addr": item.get("jibunAddress"),
        "zip_code": item.get("zipCode"),
        "sido": sido,
        "sigungu": sigungu,
        "dong": dong,
        "dong_code": _gu_code_from_sigungu(sigungu),
        "lat": lat,
        "lng": lng,
        "is_service_area": _is_seoul(sido=sido, dong_code=_gu_code_from_sigungu(sigungu)),
    }


def _naver_reverse_result(lat: float, lng: float, results: list[dict]) -> dict:
    road_result = _first_by_name(results, "roadaddr")
    addr_result = _first_by_name(results, "addr")
    adm_result = _first_by_name(results, "admcode")
    base = road_result or addr_result or adm_result or results[0]
    region = base.get("region") or {}
    land = (road_result or base).get("land") or {}
    sido = _region_name(region, "area1")
    sigungu = _region_name(region, "area2")
    dong = _region_name(region, "area3") or _region_name(region, "area4")
    dong_code = _region_code(adm_result or base)
    road_addr = _build_road_addr(region, land) if road_result else None
    jibun_addr = _build_jibun_addr(region, (addr_result or base).get("land") or land)
    return {
        "lat": lat,
        "lng": lng,
        "road_addr": road_addr,
        "road_addr_eng": None,
        "jibun_addr": jibun_addr,
        "zip_code": land.get("addition0", {}).get("value"),
        "sido": sido,
        "sigungu": sigungu,
        "dong": dong,
        "dong_code": dong_code,
        "is_service_area": _is_seoul(sido=sido, dong_code=dong_code),
        "building_name": land.get("addition1", {}).get("value"),
        "distance": 0,
    }


def _find_element(elements: list[dict], type_name: str) -> str | None:
    for element in elements:
        if type_name in (element.get("types") or []):
            return element.get("longName") or element.get("shortName")
    return None


def _first_by_name(results: list[dict], name: str) -> dict | None:
    return next((item for item in results if item.get("name") == name), None)


def _region_name(region: dict, area: str) -> str | None:
    value = region.get(area) or {}
    return value.get("name")


def _region_code(result: dict) -> str | None:
    code = result.get("code") or {}
    return code.get("id")


def _build_road_addr(region: dict, land: dict) -> str | None:
    parts = [_region_name(region, "area1"), _region_name(region, "area2"), land.get("name")]
    number = _land_number(land)
    if number:
        parts.append(number)
    text = " ".join(part for part in parts if part)
    return text or None


def _build_jibun_addr(region: dict, land: dict) -> str | None:
    parts = [_region_name(region, "area1"), _region_name(region, "area2"), _region_name(region, "area3")]
    number = _land_number(land)
    if number:
        parts.append(number)
    text = " ".join(part for part in parts if part)
    return text or None


def _land_number(land: dict) -> str | None:
    number1 = land.get("number1")
    number2 = land.get("number2")
    if number1 and number2:
        return f"{number1}-{number2}"
    return number1


def _to_float(value: str | int | float | None) -> float | None:
    return float(value) if value not in (None, "") else None


def _is_seoul(*, sido: str | None, dong_code: str | None) -> bool:
    if dong_code:
        return dong_code.startswith("11")
    return sido == "서울특별시"


def _find_gu(address: str) -> str | None:
    return next((part for part in address.split() if part.endswith("구")), None)


def _find_dong(address: str) -> str | None:
    return next((part for part in address.split() if part.endswith("동")), None)


def _client() -> GeocodingClient:
    if settings.GEOCODING_PROVIDER.lower() == "naver":
        return NaverGeocodingClient()
    return MockGeocodingClient()


async def search_address(query: str, page: int, size: int) -> dict:
    return await _client().search_address(query, page, size)


async def reverse_geocode(lat: float, lng: float) -> dict:
    return await _client().reverse_geocode(lat, lng)
