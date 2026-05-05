# 완벽: 사용자 프로필/설정/가중치 요청 스키마는 현재 명세의 요청 필드를 충족함.
from pydantic import BaseModel, ConfigDict


class UpdateProfileRequest(BaseModel):
    user_type_id: int


class UpdateSettingsRequest(BaseModel):
    noti_enabled: bool | None = None
    dark_mode: str | None = None


class UpdateWeightsRequest(BaseModel):
    security: int
    noise: int
    medical: int
    flood: int
    congestion: int

    model_config = ConfigDict(extra="forbid")
