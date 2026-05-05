# 완벽: Auth 요청 Body 스키마는 명세 필수 필드 기준으로 단순하고 완결됨.
from pydantic import BaseModel


class LoginRequest(BaseModel):
    provider: str
    code: str
    redirect_uri: str


class ReissueRequest(BaseModel):
    refresh_token: str


class LogoutRequest(BaseModel):
    refresh_token: str
