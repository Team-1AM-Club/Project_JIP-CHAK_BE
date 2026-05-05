# 완벽: 성공/실패 공통 응답 wrapper가 명세 형식에 맞고 JSON 직렬화까지 처리함.
from typing import Generic, TypeVar

from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from pydantic import BaseModel

T = TypeVar("T")


class ErrorBody(BaseModel):
    code: str
    message: str
    details: object | None = None


class SuccessResponse(BaseModel, Generic[T]):
    success: bool = True
    data: T
    error: None = None


class ErrorResponse(BaseModel):
    success: bool = False
    data: None = None
    error: ErrorBody


def success_response(data: object, status_code: int = 200) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content=jsonable_encoder({"success": True, "data": data, "error": None}),
    )


def error_response(
    code: str,
    message: str,
    status_code: int,
    details: object | None = None,
) -> JSONResponse:
    error = {"code": code, "message": message}
    if details is not None:
        error["details"] = details
    return JSONResponse(
        status_code=status_code,
        content=jsonable_encoder({"success": False, "data": None, "error": error}),
    )
