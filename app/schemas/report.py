# 완벽: 분석 요청 Body 스키마는 명세의 필수/선택 필드를 반영함.
from pydantic import BaseModel, field_validator


class AnalysisRequest(BaseModel):
    address: str
    road_addr: str | None = None
    jibun_addr: str | None = None
    lat: float
    lng: float
    dong_code: str | None = None
    source: str
    force_refresh: bool = False


class CompareAddressItem(BaseModel):
    address: str
    road_addr: str | None = None
    jibun_addr: str | None = None
    lat: float
    lng: float
    dong_code: str | None = None
    source: str


class CompareRequest(BaseModel):
    addresses: list[CompareAddressItem]

    @field_validator("addresses")
    @classmethod
    def must_be_two(cls, v: list) -> list:
        if len(v) != 2:
            raise ValueError("비교 대상 주소는 정확히 2개여야 합니다.")
        return v
