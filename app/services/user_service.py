# 불완전: 사용자 비즈니스 로직은 구현됐지만 실제 DB commit/constraint와 통합 테스트가 필요함.
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import USER_TYPE_PRESETS, user_type_by_id
from app.core.exceptions import AppException
from app.models.user import User


def weights_from_user(user: User) -> dict[str, int]:
    return {
        "security": user.security_weight,
        "noise": user.noise_weight,
        "medical": user.medical_weight,
        "flood": user.flood_weight,
        "congestion": user.congestion_weight,
    }


def is_customized(user: User) -> bool:
    preset = USER_TYPE_PRESETS[user.user_type]["preset_weights"]
    return weights_from_user(user) != preset


def profile_response(user: User) -> dict:
    current = USER_TYPE_PRESETS[user.user_type]
    return {
        "user_id": user.user_id,
        "user_name": user.user_name,
        "email": user.email,
        "current_user_type": {
            "user_type_id": current["user_type_id"],
            "user_type_name": current["user_type_name"],
            "user_type_desc": current["user_type_desc"],
            "is_customized": is_customized(user),
        },
        "current_weights": weights_from_user(user),
        "user_type_options": _user_type_options(user.user_type),
    }


async def update_profile(db: AsyncSession, user: User, user_type_id: int) -> dict:
    user_type = user_type_by_id(user_type_id)
    if user_type is None:
        raise AppException(400, "INVALID_USER_TYPE", "유효하지 않은 가구 유형입니다.")

    user.user_type = user_type
    _apply_weights(user, USER_TYPE_PRESETS[user_type]["preset_weights"])
    await db.commit()
    await db.refresh(user)
    return profile_response(user)


def settings_response(user: User) -> dict:
    return {
        "noti_enabled": user.noti_enabled,
        "dark_mode": user.dark_mode,
    }


async def update_settings(
    db: AsyncSession,
    user: User,
    noti_enabled: bool | None,
    dark_mode: str | None,
) -> dict:
    if noti_enabled is not None:
        user.noti_enabled = noti_enabled
    if dark_mode is not None:
        if dark_mode not in {"SYSTEM", "DARK", "LIGHT"}:
            raise AppException(400, "INVALID_DARK_MODE", "유효하지 않은 화면 모드입니다.")
        user.dark_mode = dark_mode
    await db.commit()
    await db.refresh(user)
    return settings_response(user)


async def update_weights(db: AsyncSession, user: User, weights: dict[str, int]) -> dict:
    missing = {"security", "noise", "medical", "flood", "congestion"} - set(weights)
    if missing:
        raise AppException(400, "MISSING_WEIGHTS", "가중치 항목을 모두 입력해 주세요.", sorted(missing))
    if any(value < 0 or value > 100 for value in weights.values()):
        raise AppException(400, "INVALID_WEIGHT_VALUE", "가중치는 0부터 100 사이여야 합니다.")
    if sum(weights.values()) != 100:
        raise AppException(400, "INVALID_WEIGHT_SUM", "가중치 합계는 100이어야 합니다.")

    _apply_weights(user, weights)
    await db.commit()
    await db.refresh(user)
    return profile_response(user)


def _apply_weights(user: User, weights: dict[str, int]) -> None:
    user.security_weight = weights["security"]
    user.noise_weight = weights["noise"]
    user.medical_weight = weights["medical"]
    user.flood_weight = weights["flood"]
    user.congestion_weight = weights["congestion"]


def _user_type_options(selected_user_type: str) -> list[dict]:
    options = []
    for user_type, preset in USER_TYPE_PRESETS.items():
        options.append(
            {
                "user_type_id": preset["user_type_id"],
                "user_type_name": preset["user_type_name"],
                "user_type_desc": preset["user_type_desc"],
                "preset_weights": preset["preset_weights"],
                "selected": user_type == selected_user_type,
            }
        )
    return options


async def withdraw(db: AsyncSession, user: User) -> dict:
    user_name = user.user_name
    withdrawn_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    
    await db.delete(user)
    await db.commit()
    
    return {
        "user_name": user_name,
        "withdrawn_at": withdrawn_at
    }
