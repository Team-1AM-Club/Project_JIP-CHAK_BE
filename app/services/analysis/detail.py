# 불완전: 전처리 기반 상세 응답 포맷은 완성했지만 raw 값은 DB 확정 전까지 기존 reports 컬럼에서 임시 매핑함.
from typing import Any

from app.core.constants import grade_from_score
from app.services.analysis.scorer import clamp_score


def status_for_score(score: int | None) -> str:
    return grade_from_score(score)


def display_value(value: Any, unit: str | None = None) -> str:
    if value is None:
        return "-"
    if isinstance(value, bool):
        return "해당" if value else "해당 없음"
    if isinstance(value, float):
        text = f"{value:.1f}".rstrip("0").rstrip(".")
    else:
        text = f"{value:,}" if isinstance(value, int) else str(value)
    return f"{text}{unit}" if unit else text


def indicator(
    *,
    key: str,
    name: str,
    raw_value: Any,
    unit: str | None,
    score: int,
    weight: float,
    display_unit: str | None = None,
) -> dict:
    return {
        "key": key,
        "name": name,
        "raw_value": raw_value,
        "display_value": display_value(raw_value, display_unit if display_unit is not None else unit),
        "unit": unit,
        "score": clamp_score(score),
        "weight": weight,
        "status": status_for_score(score),
    }


def data_source(description: str) -> dict:
    return {
        "type": "STATIC_CACHE",
        "description": description,
    }
