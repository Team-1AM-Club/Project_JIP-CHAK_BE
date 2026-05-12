from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.reference.medical import RefHealthWorkforce, RefNightClinic, RefPharmacy
from app.repositories.geo import distance_m_expr, within_radius_expr


async def nearest_clinic_distance(db: AsyncSession, lat: float, lng: float) -> float | None:
    distance = distance_m_expr(RefNightClinic.geom, lat, lng).label("distance_m")
    stmt = select(distance).order_by(distance).limit(1)
    value = await db.scalar(stmt)
    return float(value) if value is not None else None


async def count_nearby_clinics(db: AsyncSession, lat: float, lng: float, radius_m: int = 1000) -> int:
    stmt = select(func.count()).where(within_radius_expr(RefNightClinic.geom, lat, lng, radius_m))
    return int(await db.scalar(stmt) or 0)


async def count_nearby_pharmacies(db: AsyncSession, lat: float, lng: float, radius_m: int = 1000) -> int:
    stmt = select(func.count()).where(within_radius_expr(RefPharmacy.geom, lat, lng, radius_m))
    return int(await db.scalar(stmt) or 0)


async def get_health_workforce(db: AsyncSession, gu_name: str | None) -> RefHealthWorkforce | None:
    if not gu_name:
        return None
    return await db.scalar(select(RefHealthWorkforce).where(RefHealthWorkforce.gu_name == gu_name))
