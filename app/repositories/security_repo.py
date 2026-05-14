from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.reference.security import (
    RefCctv,
    RefCctvGrowth,
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


async def light_stats_nearby(db: AsyncSession, lat: float, lng: float, radius_m: int = 500) -> dict:
    base_filter = within_radius_expr(RefLightBlind.geom, lat, lng, radius_m)
    total = await db.scalar(select(func.count()).where(base_filter))
    safe_spot = await db.scalar(select(func.count()).where(base_filter, RefLightBlind.is_blind.is_(True)))
    avg_score = await db.scalar(select(func.avg(RefLightBlind.raw_score)).where(base_filter))
    return {
        "nearby_count": int(total or 0),
        "safe_spot_count": int(safe_spot or 0),
        "avg_safe_bonus_score": round(float(avg_score), 1) if avg_score is not None else None,
        "radius_m": radius_m,
    }


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


async def nearest_police_detail(db: AsyncSession, lat: float, lng: float) -> dict | None:
    distance = distance_m_expr(RefPolice.geom, lat, lng).label("distance_m")
    stmt = (
        select(RefPolice.office_name, RefPolice.station, RefPolice.category, distance)
        .where(RefPolice.geom.is_not(None))
        .order_by(distance)
        .limit(1)
    )
    row = (await db.execute(stmt)).first()
    if row is None:
        return None
    office_name, station, category, distance_m = row
    return {
        "name": office_name or station or category or "가까운 파출소",
        "distance_m": float(distance_m),
    }


async def get_police_score(db: AsyncSession, gu_name: str | None) -> float | None:
    if not gu_name:
        return None
    stmt = select(func.avg(RefPolice.raw_score)).where(RefPolice.address.contains(gu_name))
    value = await db.scalar(stmt)
    return float(value) if value is not None else None


async def get_police_score_nearby(
    db: AsyncSession,
    lat: float,
    lng: float,
    gu_name: str | None,
    radius_m: int = 1000,
) -> float | None:
    nearby_stmt = select(func.avg(RefPolice.raw_score)).where(
        RefPolice.geom.is_not(None),
        within_radius_expr(RefPolice.geom, lat, lng, radius_m),
    )
    value = await db.scalar(nearby_stmt)
    if value is not None:
        return float(value)

    distance = distance_m_expr(RefPolice.geom, lat, lng).label("distance_m")
    nearest_stmt = (
        select(RefPolice.raw_score)
        .where(RefPolice.geom.is_not(None), RefPolice.raw_score.is_not(None))
        .order_by(distance)
        .limit(1)
    )
    value = await db.scalar(nearest_stmt)
    if value is not None:
        return float(value)

    return await get_police_score(db, gu_name)


async def get_crime_score(db: AsyncSession, gu_name: str | None) -> RefCrime | None:
    if not gu_name:
        return None
    return await db.scalar(select(RefCrime).where(RefCrime.gu_name == gu_name))


async def get_cctv_growth_score(db: AsyncSession, gu_name: str | None) -> RefCctvGrowth | None:
    if not gu_name:
        return None
    return await db.scalar(select(RefCctvGrowth).where(RefCctvGrowth.gu_name == gu_name))


async def get_police_pop_score(db: AsyncSession, gu_name: str | None) -> RefPolicePopulation | None:
    if not gu_name:
        return None
    return await db.scalar(select(RefPolicePopulation).where(RefPolicePopulation.gu_name == gu_name))


async def get_safepath_score(db: AsyncSession, region_code: str | None) -> RefSafePath | None:
    if not region_code:
        return None
    exact = await db.scalar(select(RefSafePath).where(RefSafePath.region_code == region_code))
    if exact is not None:
        return exact

    prefix = str(region_code)[:5]
    value = await db.scalar(
        select(func.avg(RefSafePath.raw_score)).where(RefSafePath.region_code.startswith(prefix))
    )
    if value is None:
        return None
    return RefSafePath(region_code=prefix, raw_score=float(value))
