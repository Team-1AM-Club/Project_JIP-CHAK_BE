# 완벽: Auth 요청 Body 스키마는 Google-only MVP 정책과 명세 필수 필드를 반영함.
from typing import Literal

from pydantic import BaseModel


class LoginRequest(BaseModel):
    provider: Literal["google"]
    code: str
    redirect_uri: str


class ReissueRequest(BaseModel):
    refresh_token: str


class LogoutRequest(BaseModel):
    refresh_token: str
