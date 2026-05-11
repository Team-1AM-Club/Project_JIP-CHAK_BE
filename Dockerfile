# Stage 1: Build dependencies
FROM python:3.11-slim as builder

WORKDIR /app

# 시스템 의존성 설치 (geoalchemy2, asyncpg 및 shapely C 확장 빌드용)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libgeos-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
# 의존성을 패키징 (캐시 활용 및 빌드 산출물 분리)
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /app/wheels -r requirements.txt

# Stage 2: Production image
FROM python:3.11-slim

# 환경 변수 설정
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

WORKDIR /app

# 런타임용 시스템 라이브러리 설치 (shapely, postgis 연동 등)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgeos-c1v5 \
    && rm -rf /var/lib/apt/lists/*

# 빌더 스테이지에서 컴파일된 패키지 복사 및 설치
COPY --from=builder /app/wheels /wheels
COPY --from=builder /app/requirements.txt .
RUN pip install --no-cache /wheels/*

# Non-root 사용자 생성 (보안 강화)
RUN adduser --disabled-password --gecos '' appuser && \
    chown -R appuser:appuser /app

# 애플리케이션 코드 및 데이터 복사 (data 폴더 포함 - DB Seeding용)
COPY --chown=appuser:appuser . .

# 권한 변경
USER appuser

EXPOSE 8000

# 프로덕션 서버 실행 (Uvicorn 워커 4개 구동)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4", "--proxy-headers"]