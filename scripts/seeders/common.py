from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd
from geoalchemy2.shape import from_shape
from shapely.geometry import Point
from sqlalchemy import delete, func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession


def load_csv(path: Path) -> pd.DataFrame:
    for encoding in ("utf-8-sig", "euc-kr"):
        try:
            return pd.read_csv(path, encoding=encoding)
        except UnicodeDecodeError:
            continue
    return pd.read_csv(path)


def make_point(lon: Any, lat: Any):
    if pd.isna(lon) or pd.isna(lat):
        return None
    return from_shape(Point(float(lon), float(lat)), srid=4326)


def int_or_none(value: Any) -> int | None:
    if pd.isna(value):
        return None
    return int(float(value))


def float_or_none(value: Any) -> float | None:
    if pd.isna(value):
        return None
    return float(value)


def str_or_none(value: Any) -> str | None:
    if pd.isna(value):
        return None
    return str(value)


async def seed_table(
    session: AsyncSession,
    model,
    records: list[dict],
    *,
    replace: bool = False,
    batch_size: int = 1000,
) -> int:
    if replace:
        await session.execute(delete(model))

    records = [record for record in records if record.get("geom", True) is not None]

    existing_count = await session.scalar(select(func.count()).select_from(model))
    if existing_count and not replace:
        return 0

    if not records:
        return 0

    for start in range(0, len(records), batch_size):
        batch = records[start:start + batch_size]
        stmt = insert(model).values(batch).on_conflict_do_nothing()
        await session.execute(stmt)
    await session.commit()
    return len(records)
