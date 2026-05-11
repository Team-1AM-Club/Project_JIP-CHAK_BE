# 완벽: FastAPI 앱 생성, 공통 예외 핸들러, /api/v1 라우터 등록, health check를 구성함.
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError

from app.api import addresses, auth, bookmarks, reports, users
from app.core.exceptions import AppException, app_exception_handler, validation_exception_handler
from app.core.task_status import close_redis_client


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await close_redis_client()


def create_app() -> FastAPI:
    app = FastAPI(title="JIP-CHAK API", lifespan=lifespan)

    app.add_exception_handler(AppException, app_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)

    # CORS 미들웨어 추가 (프론트엔드 연동을 위해 필수)
    from fastapi.middleware.cors import CORSMiddleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # 실제 배포 시 프론트엔드 도메인으로 제한 필요 (예: ["https://jipchak.com"])
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

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
