#!/bin/sh

# 데이터베이스 마이그레이션 실행 (서버 구동 시 최신 스키마로 유지)
echo "Running database migrations..."
alembic upgrade head

# Uvicorn 실행 (GCP Cloud Run 등에서 주입해주는 PORT 변수를 사용하도록 바인딩)
# 기본 포트는 8080으로 설정
PORT=${PORT:-8080}
echo "Starting server on port $PORT..."
exec uvicorn app.main:app --host 0.0.0.0 --port $PORT
