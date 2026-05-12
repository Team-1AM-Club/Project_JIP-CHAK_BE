from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.reference.flood import RefFloodPump, RefFloodTrace, RefImpervious
from app.repositories.geo import distance_m_expr, point_expr


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
