from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.reference.congestion import RefBusStop, RefFloatingPopulation, RefSubwayCongestion
from app.repositories.geo import within_radius_expr


async def avg_nearby_bus_congestion(db: AsyncSession, lat: float, lng: float, radius_m: int = 500) -> float | None:
    stmt = select(func.avg(RefBusStop.raw_score)).where(
        within_radius_expr(RefBusStop.geom, lat, lng, radius_m)
    )
    value = await db.scalar(stmt)
    return float(value) if value is not None else None


async def get_floating_pop(db: AsyncSession, dong_code: str | None) -> float | None:
    if dong_code:
        stmt = select(RefFloatingPopulation.total_pop).where(RefFloatingPopulation.dong_code == dong_code)
        value = await db.scalar(stmt)
        if value is not None:
            return float(value)
    # Fallback to average if dong_code is corrupted or missing
    stmt = select(func.avg(RefFloatingPopulation.total_pop))
    value = await db.scalar(stmt)
    return float(value) if value is not None else None


async def get_subway_congestion(db: AsyncSession, station_name: str | None) -> RefSubwayCongestion | None:
    if not station_name:
        return None
    return await db.scalar(
        select(RefSubwayCongestion).where(RefSubwayCongestion.station_name == station_name)
    )

async def get_avg_subway_congestion(db: AsyncSession) -> float | None:
    stmt = select(func.avg(RefSubwayCongestion.raw_score))
    value = await db.scalar(stmt)
    return float(value) if value is not None else None
