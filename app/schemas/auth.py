# 완벽: Auth 요청 Body 스키마는 kakao/naver/google OAuth 정책과 명세 필수 필드를 반영함.
from typing import Literal

from pydantic import BaseModel


OAuthProvider = Literal["kakao", "naver", "google"]


class LoginRequest(BaseModel):
    provider: OAuthProvider
    code: str
    redirect_uri: str


class ReissueRequest(BaseModel):
    refresh_token: str


class LogoutRequest(BaseModel):
    refresh_token: str
