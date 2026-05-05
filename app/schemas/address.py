# 불완전: 주소/비교 관련 보조 스키마만 정의되어 있고 실제 외부 주소 API 응답 모델 확정 후 보강이 필요함.
from uuid import UUID

from pydantic import BaseModel


class AddressSearchResult(BaseModel):
    road_addr: str
    jibun_addr: str | None = None
    zip_code: str | None = None
    sido: str
    sigungu: str | None = None
    dong: str | None = None
    dong_code: str | None = None
    lat: float | None = None
    lng: float | None = None
    is_service_area: bool


class CompareQuery(BaseModel):
    report_ids: list[UUID]
