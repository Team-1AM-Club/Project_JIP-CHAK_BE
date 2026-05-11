# 완벽: 분석 요청 Body 스키마는 명세의 필수/선택 필드를 반영함.
from pydantic import BaseModel


class AnalysisRequest(BaseModel):
    address: str
    road_addr: str | None = None
    jibun_addr: str | None = None
    lat: float
    lng: float
    dong_code: str | None = None
    source: str
    force_refresh: bool = False
