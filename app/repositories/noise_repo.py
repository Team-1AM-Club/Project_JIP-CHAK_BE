from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.reference.noise import (
    RefNoiseAircraft,
    RefNoiseComplaint,
    RefNoiseHourly,
    RefNoiseIdwGrid,
    RefNoiseLdenPoint,
    RefNoiseMeasurement,
    RefNoisePub,
    RefNoiseRail,
    RefNoiseRoad,
    RefNoiseTrafficPoint,
)
from app.repositories.geo import distance_m_expr, within_radius_expr


async def count_nearby_pubs(db: AsyncSession, lat: float, lng: float, radius_m: int = 500) -> int:
    stmt = select(func.count()).where(within_radius_expr(RefNoisePub.geom, lat, lng, radius_m))
    return int(await db.scalar(stmt) or 0)


async def get_noise_complaint(db: AsyncSession, gu_name: str | None) -> RefNoiseComplaint | None:
    if not gu_name:
        return None
    return await db.scalar(select(RefNoiseComplaint).where(RefNoiseComplaint.gu_name == gu_name))


async def get_avg_noise_complaint(db: AsyncSession) -> float | None:
    stmt = select(func.avg(RefNoiseComplaint.raw_score))
    value = await db.scalar(stmt)
    return float(value) if value is not None else None


async def get_avg_noise_measurement(db: AsyncSession) -> float | None:
    stmt = select(func.avg(RefNoiseMeasurement.leq))
    value = await db.scalar(stmt)
    return float(value) if value is not None else None


async def get_nearest_idw_noise(db: AsyncSession, lat: float, lng: float) -> float | None:
    distance = distance_m_expr(RefNoiseIdwGrid.geom, lat, lng).label("distance_m")
    stmt = (
        select(RefNoiseIdwGrid.estimated_db)
        .order_by(distance)
        .limit(1)
    )
    value = await db.scalar(stmt)
    return float(value) if value is not None else None


async def get_nearest_lden_noise(db: AsyncSession, lat: float, lng: float) -> float | None:
    distance = distance_m_expr(RefNoiseLdenPoint.geom, lat, lng).label("distance_m")
    stmt = (
        select(RefNoiseLdenPoint.raw_score)
        .where(RefNoiseLdenPoint.raw_score.is_not(None))
        .order_by(distance)
        .limit(1)
    )
    value = await db.scalar(stmt)
    return float(value) if value is not None else None


async def get_nearest_traffic_noise(db: AsyncSession, lat: float, lng: float) -> float | None:
    distance = distance_m_expr(RefNoiseTrafficPoint.geom, lat, lng).label("distance_m")
    stmt = (
        select(RefNoiseTrafficPoint.raw_score)
        .where(RefNoiseTrafficPoint.raw_score.is_not(None))
        .order_by(distance)
        .limit(1)
    )
    value = await db.scalar(stmt)
    return float(value) if value is not None else None


async def get_nearest_traffic_noise_detail(db: AsyncSession, lat: float, lng: float) -> dict | None:
    distance = distance_m_expr(RefNoiseTrafficPoint.geom, lat, lng).label("distance_m")
    stmt = (
        select(RefNoiseTrafficPoint, distance)
        .where(RefNoiseTrafficPoint.raw_score.is_not(None))
        .order_by(distance)
        .limit(1)
    )
    row = (await db.execute(stmt)).first()
    if row is None:
        return None
    point, distance_m = row
    return {
        "point_no": point.point_no,
        "point_name": point.point_name,
        "daily_traffic": _float_or_none(point.daily_traffic),
        "night_traffic": _float_or_none(point.night_traffic),
        "raw_score": _float_or_none(point.raw_score),
        "lat": _float_or_none(point.lat),
        "lon": _float_or_none(point.lon),
        "distance_m": float(distance_m),
    }


async def get_nearest_measurement_detail(db: AsyncSession, lat: float, lng: float) -> dict | None:
    distance = distance_m_expr(RefNoiseMeasurement.geom, lat, lng).label("distance_m")
    stmt = (
        select(RefNoiseMeasurement, distance)
        .where(RefNoiseMeasurement.geom.is_not(None))
        .order_by(distance)
        .limit(1)
    )
    row = (await db.execute(stmt)).first()
    if row is None:
        return None
    measurement, distance_m = row
    return {
        "station": measurement.station,
        "address": measurement.address,
        "land_use": measurement.land_use,
        "leq": _float_or_none(measurement.leq),
        "raw_score": _float_or_none(measurement.raw_score),
        "lat": _float_or_none(measurement.lat),
        "lon": _float_or_none(measurement.lon),
        "radius_m": _float_or_none(measurement.radius_m),
        "distance_m": float(distance_m),
    }


async def get_hourly_noise_by_station(db: AsyncSession, station: str | None) -> list[dict]:
    if not station:
        return []
    stmt = (
        select(RefNoiseHourly)
        .where(RefNoiseHourly.station == station)
        .order_by(RefNoiseHourly.hour)
    )
    rows = (await db.scalars(stmt)).all()
    return [
        {
            "station": row.station,
            "hour": row.hour,
            "raw_score": _float_or_none(row.raw_score),
            "time_penalty": _float_or_none(row.time_penalty),
            "lden_score": _float_or_none(row.lden_score),
        }
        for row in rows
    ]


async def get_road_noise_score(db: AsyncSession, gu_name: str | None) -> float | None:
    if not gu_name:
        return None
    stmt = select(func.avg(RefNoiseRoad.raw_score)).where(RefNoiseRoad.region.contains(gu_name))
    value = await db.scalar(stmt)
    return float(value) if value is not None else None


async def get_avg_aircraft_noise(db: AsyncSession) -> float | None:
    stmt = select(func.avg(RefNoiseAircraft.raw_score))
    value = await db.scalar(stmt)
    return float(value) if value is not None else None


async def get_avg_rail_noise(db: AsyncSession) -> float | None:
    stmt = select(func.avg(RefNoiseRail.raw_score))
    value = await db.scalar(stmt)
    return float(value) if value is not None else None


async def get_avg_hourly_noise(db: AsyncSession) -> float | None:
    stmt = select(func.avg(RefNoiseHourly.raw_score))
    value = await db.scalar(stmt)
    return float(value) if value is not None else None


def _float_or_none(value) -> float | None:
    return float(value) if value is not None else None
