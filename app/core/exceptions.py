# 완벽: 공통 Response 규격에 맞춘 AppException 및 validation handler가 구현되고 보호 API 응답으로 검증됨.
from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.schemas.common import error_response


class AppException(Exception):
    def __init__(
        self,
        status_code: int,
        code: str,
        message: str,
        details: object | None = None,
    ) -> None:
        self.status_code = status_code
        self.code = code
        self.message = message
        self.details = details


async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    return error_response(exc.code, exc.message, exc.status_code, exc.details)


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    return error_response(
        "INVALID_INPUT_VALUE",
        "유효하지 않은 입력 값입니다.",
        400,
        exc.errors(),
    )


def UnauthorizedError() -> AppException:
    return AppException(401, "UNAUTHORIZED", "인증이 필요합니다.")


def InvalidTokenError() -> AppException:
    return AppException(401, "INVALID_TOKEN", "유효하지 않은 토큰입니다.")


def ExpiredTokenError() -> AppException:
    return AppException(401, "EXPIRED_TOKEN", "토큰이 만료되었습니다.")


def ForbiddenError(message: str = "권한이 없습니다.") -> AppException:
    return AppException(403, "FORBIDDEN", message)


def ForbiddenReportError() -> AppException:
    return AppException(403, "FORBIDDEN_REPORT", "해당 리포트에 접근할 수 없습니다.")


def UserNotFoundError() -> AppException:
    return AppException(404, "USER_NOT_FOUND", "사용자를 찾을 수 없습니다.")


def ReportNotFoundError() -> AppException:
    return AppException(404, "REPORT_NOT_FOUND", "리포트를 찾을 수 없습니다.")


def InvalidInputError(details: object | None = None) -> AppException:
    return AppException(400, "INVALID_INPUT_VALUE", "유효하지 않은 입력 값입니다.", details)


def ExternalApiError(message: str = "외부 데이터 조회 중 오류가 발생했습니다.") -> AppException:
    return AppException(500, "EXTERNAL_API_ERROR", message)


def InternalServerError() -> AppException:
    return AppException(500, "INTERNAL_SERVER_ERROR", "서버 내부 오류가 발생했습니다.")
