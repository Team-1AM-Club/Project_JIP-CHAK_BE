from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.reference.noise import RefNoiseComplaint, RefNoiseMeasurement, RefNoisePub
from app.repositories.geo import within_radius_expr


async def count_nearby_pubs(db: AsyncSession, lat: float, lng: float, radius_m: int = 500) -> int:
    stmt = select(func.count()).where(within_radius_expr(RefNoisePub.geom, lat, lng, radius_m))
    return int(await db.scalar(stmt) or 0)


async def get_noise_complaint(db: AsyncSession, gu_name: str | None) -> RefNoiseComplaint | None:
    if not gu_name:
        return None
    return await db.scalar(select(RefNoiseComplaint).where(RefNoiseComplaint.gu_name == gu_name))


async def get_avg_noise_measurement(db: AsyncSession) -> float | None:
    stmt = select(func.avg(RefNoiseMeasurement.leq))
    value = await db.scalar(stmt)
    return float(value) if value is not None else None
