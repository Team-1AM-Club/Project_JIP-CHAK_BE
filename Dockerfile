# syntax=docker/dockerfile:1.6

# Stage 1: Build dependencies
FROM python:3.11-slim AS builder

WORKDIR /app

# 빌드 의존성 (geoalchemy2, asyncpg, shapely C 확장용)
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        libgeos-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# 의존성 wheel 패키징
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /app/wheels -r requirements.txt


# Stage 2: Production image
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# 런타임 라이브러리 + healthcheck용 curl
RUN apt-get update && apt-get install -y --no-install-recommends \
        libgeos-c1v5 \
        curl \
    && rm -rf /var/lib/apt/lists/*

# 빌더 스테이지 wheel 복사 후 설치
COPY --from=builder /app/wheels /wheels
COPY --from=builder /app/requirements.txt .
RUN pip install --no-cache /wheels/* && rm -rf /wheels

# Non-root 사용자
RUN adduser --disabled-password --gecos '' appuser

# 애플리케이션 코드 복사
COPY --chown=appuser:appuser . .

USER appuser

EXPOSE 8000

# 헬스체크 (컨테이너 자체 상태 모니터링)
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD curl -fsS http://localhost:8000/health || exit 1

CMD ["uvicorn", "app.main:app", \
     "--host", "0.0.0.0", \
     "--port", "8000", \
     "--workers", "4", \
     "--proxy-headers", \
     "--forwarded-allow-ips=*"]
