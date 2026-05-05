# 불완전: Redis 상태 저장을 우선 사용하지만 로컬 Redis 부재 시 개발용 in-memory fallback을 사용함.
import json
from uuid import UUID

from fastapi.encoders import jsonable_encoder
from redis.asyncio import Redis
from redis.exceptions import RedisError

from app.core.config import settings

_fallback_statuses: dict[str, dict] = {}
_redis_client: Redis | None = None


async def set_task_status(task_id: UUID, status: dict, ttl_seconds: int = 3600) -> None:
    key = _task_key(task_id)
    payload = json.dumps(jsonable_encoder(status), ensure_ascii=False)
    try:
        client = _get_redis_client()
        await client.set(key, payload, ex=ttl_seconds)
    except RedisError:
        _fallback_statuses[key] = json.loads(payload)


async def get_task_status(task_id: UUID) -> dict | None:
    key = _task_key(task_id)
    try:
        client = _get_redis_client()
        raw_status = await client.get(key)
        if raw_status is not None:
            return json.loads(raw_status)
    except RedisError:
        return _fallback_statuses.get(key)
    return _fallback_statuses.get(key)


async def close_redis_client() -> None:
    global _redis_client
    if _redis_client is not None:
        await _redis_client.aclose()
        _redis_client = None


def _get_redis_client() -> Redis:
    global _redis_client
    if _redis_client is None:
        _redis_client = Redis.from_url(settings.REDIS_URL, decode_responses=True)
    return _redis_client


def _task_key(task_id: UUID) -> str:
    return f"task:{task_id}"
