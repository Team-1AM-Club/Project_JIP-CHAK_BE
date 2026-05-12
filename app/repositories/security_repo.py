from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.reference.security import (
    RefCctv,
    RefCrime,
    RefLightBlind,
    RefPolice,
    RefPolicePopulation,
    RefSafePath,
)
from app.repositories.geo import distance_m_expr, within_radius_expr


async def count_nearby_cctv(db: AsyncSession, lat: float, lng: float, radius_m: int = 500) -> int:
    stmt = select(func.count()).where(within_radius_expr(RefCctv.geom, lat, lng, radius_m))
    return int(await db.scalar(stmt) or 0)


async def avg_light_blind_score(db: AsyncSession, lat: float, lng: float, radius_m: int = 500) -> float | None:
    stmt = select(func.avg(RefLightBlind.raw_score)).where(
        within_radius_expr(RefLightBlind.geom, lat, lng, radius_m)
    )
    value = await db.scalar(stmt)
    return float(value) if value is not None else None


async def nearest_police_distance(db: AsyncSession, lat: float, lng: float) -> float | None:
    distance = distance_m_expr(RefPolice.geom, lat, lng).label("distance_m")
    stmt = (
        select(distance)
        .where(RefPolice.geom.is_not(None))
        .order_by(distance)
        .limit(1)
    )
    value = await db.scalar(stmt)
    return float(value) if value is not None else None


async def get_crime_score(db: AsyncSession, gu_name: str | None) -> RefCrime | None:
    if not gu_name:
        return None
    return await db.scalar(select(RefCrime).where(RefCrime.gu_name == gu_name))


async def get_police_pop_score(db: AsyncSession, gu_name: str | None) -> RefPolicePopulation | None:
    if not gu_name:
        return None
    return await db.scalar(select(RefPolicePopulation).where(RefPolicePopulation.gu_name == gu_name))


async def get_safepath_score(db: AsyncSession, region_code: str | None) -> RefSafePath | None:
    if not region_code:
        return None
    return await db.scalar(select(RefSafePath).where(RefSafePath.region_code == region_code))
