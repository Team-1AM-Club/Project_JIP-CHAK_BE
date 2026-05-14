from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.meta_stats import get_stat
from app.models.reference.flood import (
    RefFloodDefense,
    RefFloodPump,
    RefFloodTrace,
    RefFloodTracePoint,
    RefFloodTraceSummary,
    RefImpervious,
)
from app.repositories.geo import distance_m_expr, point_expr, within_radius_expr


async def is_in_flood_trace(db: AsyncSession, lat: float, lng: float) -> bool:
    stmt = select(func.count()).where(func.ST_Intersects(RefFloodTrace.geom, point_expr(lat, lng)))
    return bool(await db.scalar(stmt) or 0)


async def nearest_pump_distance(db: AsyncSession, lat: float, lng: float) -> float | None:
    distance = distance_m_expr(RefFloodPump.geom, lat, lng).label("distance_m")
    stmt = select(distance).order_by(distance).limit(1)
    value = await db.scalar(stmt)
    return float(value) if value is not None else None


async def nearest_pump_capacity(db: AsyncSession, lat: float, lng: float) -> float | None:
    distance = distance_m_expr(RefFloodPump.geom, lat, lng).label("distance_m")
    stmt = select(RefFloodPump.max_capacity).order_by(distance).limit(1)
    value = await db.scalar(stmt)
    return float(value) if value is not None else None


async def get_impervious_ratio(db: AsyncSession, gu_name: str | None) -> float | None:
    if not gu_name:
        return None
    stmt = select(RefImpervious.impervious_ratio).where(RefImpervious.gu_name == gu_name)
    value = await db.scalar(stmt)
    return float(value) if value is not None else None


async def get_flood_defense(db: AsyncSession, gu_name: str | None) -> RefFloodDefense | None:
    if not gu_name:
        return None
    stmt = select(RefFloodDefense).where(RefFloodDefense.gu_name == gu_name)
    return await db.scalar(stmt)


async def get_flood_defense_average_score(db: AsyncSession) -> float | None:
    values = (
        await db.scalars(
            select(RefFloodDefense.raw_score).where(RefFloodDefense.raw_score.isnot(None))
        )
    ).all()
    scores = [_normalize_flood_defense(value) for value in values]
    scores = [score for score in scores if score is not None]
    return round(sum(scores) / len(scores), 1) if scores else None


async def get_flood_defense_top_percent(db: AsyncSession, gu_name: str | None) -> int | None:
    defense = await get_flood_defense(db, gu_name)
    if defense is None or defense.raw_score is None:
        return None
    scores = [
        float(score)
        for score in (
            await db.scalars(
                select(RefFloodDefense.raw_score).where(RefFloodDefense.raw_score.isnot(None))
            )
        ).all()
    ]
    if not scores:
        return None
    better_count = sum(1 for score in scores if score > float(defense.raw_score))
    return max(1, round((better_count + 1) / len(scores) * 100))


async def get_flood_trace_summary(db: AsyncSession, gu_name: str | None) -> RefFloodTraceSummary | None:
    if not gu_name:
        return None
    stmt = select(RefFloodTraceSummary).where(RefFloodTraceSummary.gu_name == gu_name)
    return await db.scalar(stmt)


async def get_flood_trace_average_count(db: AsyncSession) -> float | None:
    value = await db.scalar(select(func.avg(RefFloodTraceSummary.flood_count)))
    return round(float(value), 1) if value is not None else None


async def get_flood_trace_year_counts(db: AsyncSession, gu_name: str | None) -> list[dict]:
    if not gu_name:
        return []
    stmt = (
        select(RefFloodTracePoint.flood_year, func.count())
        .where(RefFloodTracePoint.gu_name == gu_name)
        .group_by(RefFloodTracePoint.flood_year)
        .order_by(RefFloodTracePoint.flood_year)
    )
    rows = (await db.execute(stmt)).all()
    return [
        {"year": int(year), "count": int(count)}
        for year, count in rows
        if year is not None
    ]


async def get_flood_trace_events(db: AsyncSession, gu_name: str | None, *, limit: int = 3) -> list[dict]:
    if not gu_name:
        return []
    stmt = (
        select(RefFloodTracePoint)
        .where(RefFloodTracePoint.gu_name == gu_name)
        .order_by(RefFloodTracePoint.flood_year.desc(), RefFloodTracePoint.flood_area_m2.desc())
        .limit(limit)
    )
    points = (await db.scalars(stmt)).all()
    return [
        {
            "year": point.flood_year,
            "address": point.address,
            "flood_type": point.flood_type,
            "area_m2": float(point.flood_area_m2) if point.flood_area_m2 is not None else None,
            "depth_cm": float(point.flood_depth_cm) if point.flood_depth_cm is not None else None,
        }
        for point in points
    ]


async def count_nearby_flood_trace_points(
    db: AsyncSession,
    lat: float,
    lng: float,
    *,
    radius_m: int = 500,
) -> int:
    stmt = select(func.count()).where(within_radius_expr(RefFloodTracePoint.geom, lat, lng, radius_m))
    return int(await db.scalar(stmt) or 0)


def _normalize_flood_defense(value: float | None) -> int | None:
    if value is None:
        return None
    stat = get_stat("flood_defense")
    if not stat or stat["p95"] == stat["p05"]:
        return max(0, min(100, round(float(value) * 100)))
    score = (float(value) - stat["p05"]) / (stat["p95"] - stat["p05"]) * 100
    return max(0, min(100, round(score)))
