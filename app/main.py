# 완벽: FastAPI 앱 생성, 공통 예외 핸들러, /api/v1 라우터 등록, health check는 import/OpenAPI 검증까지 완료됨.
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError

from app.api import addresses, auth, bookmarks, reports, users
from app.core.exceptions import AppException, app_exception_handler, validation_exception_handler


def create_app() -> FastAPI:
    app = FastAPI(title="JIP-CHAK API")

    app.add_exception_handler(AppException, app_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)

    app.include_router(auth.router, prefix="/api/v1")
    app.include_router(users.router, prefix="/api/v1")
    app.include_router(addresses.router, prefix="/api/v1")
    app.include_router(reports.router, prefix="/api/v1")
    app.include_router(bookmarks.router, prefix="/api/v1")

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
