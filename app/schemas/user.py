# 완벽: 사용자 프로필/설정/가중치 요청 스키마는 현재 API 계약을 반영함.
from pydantic import BaseModel, ConfigDict, Field


class UpdateProfileRequest(BaseModel):
    user_type_id: int = Field(ge=1, le=3)


class UpdateSettingsRequest(BaseModel):
    noti_enabled: bool | None = None
    dark_mode: str | None = None


class UpdateWeightsRequest(BaseModel):
    security: int = Field(ge=0, le=100)
    noise: int = Field(ge=0, le=100)
    medical: int = Field(ge=0, le=100)
    flood: int = Field(ge=0, le=100)
    congestion: int = Field(ge=0, le=100)

    model_config = ConfigDict(extra="forbid")
