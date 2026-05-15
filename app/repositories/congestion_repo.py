from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.reference.congestion import (
    RefBusHourly,
    RefBusStop,
    RefFloatingPopulation,
    RefSubwayCongestion,
)
from app.repositories.geo import distance_m_expr, within_radius_expr


async def avg_nearby_bus_congestion(db: AsyncSession, lat: float, lng: float, radius_m: int = 500) -> float | None:
    stmt = select(func.avg(RefBusStop.raw_score)).where(
        within_radius_expr(RefBusStop.geom, lat, lng, radius_m)
    )
    value = await db.scalar(stmt)
    return float(value) if value is not None else None


async def get_floating_pop(db: AsyncSession, dong_code: str | None) -> float | None:
    if dong_code:
        code = str(dong_code)
        stmt = select(RefFloatingPopulation.total_pop).where(RefFloatingPopulation.dong_code == code)
        value = await db.scalar(stmt)
        if value is not None:
            return float(value)

        prefix = code[:5]
        stmt = select(func.avg(RefFloatingPopulation.total_pop)).where(
            RefFloatingPopulation.dong_code.startswith(prefix)
        )
        value = await db.scalar(stmt)
        if value is not None:
            return float(value)
    # Fallback to average if dong_code is corrupted or missing
    stmt = select(func.avg(RefFloatingPopulation.total_pop))
    value = await db.scalar(stmt)
    return float(value) if value is not None else None


async def get_floating_population_detail(db: AsyncSession, dong_code: str | None) -> dict | None:
    row = await _get_floating_population_row(db, dong_code)
    if row is None:
        return None
    return {
        "dong_code": row.dong_code,
        "total_pop": float(row.total_pop or 0.0),
        "raw_score": float(row.raw_score or 0.0),
        "hourly_pop": row.hourly_pop or {},
    }


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


async def nearest_subway_station(db: AsyncSession, lat: float, lng: float) -> dict | None:
    distance = distance_m_expr(RefSubwayCongestion.geom, lat, lng).label("distance_m")
    stmt = (
        select(RefSubwayCongestion, distance)
        .where(RefSubwayCongestion.geom.is_not(None))
        .order_by(distance)
        .limit(1)
    )
    row = (await db.execute(stmt)).first()
    if row is None:
        return None
    station, distance_m = row
    return {
        "line_name": station.line_name,
        "station_no": station.station_no,
        "station_name": station.station_name,
        "distance_m": float(distance_m),
        "daily_passengers_total": _float_or_none(station.daily_passengers_total),
        "daily_passengers_weekday": _float_or_none(station.daily_passengers_weekday),
        "daily_passengers_weekend": _float_or_none(station.daily_passengers_weekend),
        "avg_congestion_total": _float_or_none(station.avg_congestion_total),
        "avg_congestion_weekday": _float_or_none(station.avg_congestion_weekday),
        "avg_congestion_weekend": _float_or_none(station.avg_congestion_weekend),
        "peak_congestion_total": _float_or_none(station.peak_congestion_total),
        "peak_congestion_weekday": _float_or_none(station.peak_congestion_weekday),
        "peak_congestion_weekend": _float_or_none(station.peak_congestion_weekend),
        "raw_score": _float_or_none(station.raw_score),
    }


async def nearest_bus_stop(db: AsyncSession, lat: float, lng: float) -> dict | None:
    distance = distance_m_expr(RefBusStop.geom, lat, lng).label("distance_m")
    stmt = (
        select(RefBusStop, distance)
        .order_by(distance)
        .limit(1)
    )
    row = (await db.execute(stmt)).first()
    if row is None:
        return None
    stop, distance_m = row
    return {
        "node_id": stop.node_id,
        "ars_id": stop.ars_id,
        "stop_name": stop.stop_name,
        "stop_type": stop.stop_type,
        "distance_m": float(distance_m),
        "daily_avg_usage": _float_or_none(stop.daily_avg_usage),
        "raw_score": _float_or_none(stop.raw_score),
    }


async def nearby_bus_hourly_average(
    db: AsyncSession,
    lat: float,
    lng: float,
    radius_m: int = 500,
) -> dict:
    stmt = select(RefBusHourly.hourly_pop).where(within_radius_expr(RefBusHourly.geom, lat, lng, radius_m))
    rows = (await db.scalars(stmt)).all()
    totals: dict[str, float] = {}
    counts: dict[str, int] = {}
    for hourly in rows:
        for hour, value in (hourly or {}).items():
            if value is None:
                continue
            totals[hour] = totals.get(hour, 0.0) + float(value)
            counts[hour] = counts.get(hour, 0) + 1
    return {
        "radius_m": radius_m,
        "stop_count": len(rows),
        "hourly_pop": {
            hour: round(totals[hour] / counts[hour], 1)
            for hour in sorted(totals.keys())
            if counts.get(hour)
        },
    }


async def _get_floating_population_row(
    db: AsyncSession,
    dong_code: str | None,
) -> RefFloatingPopulation | None:
    if dong_code:
        code = str(dong_code)
        row = await db.scalar(select(RefFloatingPopulation).where(RefFloatingPopulation.dong_code == code))
        if row is not None:
            return row

        prefix = code[:5]
        row = await db.scalar(
            select(RefFloatingPopulation)
            .where(RefFloatingPopulation.dong_code.startswith(prefix))
            .order_by(RefFloatingPopulation.total_pop.desc())
            .limit(1)
        )
        if row is not None:
            return row
    return await db.scalar(select(RefFloatingPopulation).order_by(RefFloatingPopulation.total_pop.desc()).limit(1))


def _float_or_none(value) -> float | None:
    return float(value) if value is not None else None
