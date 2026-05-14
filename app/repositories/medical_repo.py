from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.reference.medical import RefHealthDong, RefHealthWorkforce, RefNightClinic, RefPharmacy
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


async def nearest_medical_facilities(db: AsyncSession, lat: float, lng: float) -> dict:
    return {
        "general_hospital": await _nearest_clinic_by_types(db, lat, lng, ["종합병원"]),
        "hospital": await _nearest_clinic_by_types(db, lat, lng, ["병원", "종합병원"]),
        "clinic": await _nearest_clinic_by_types(db, lat, lng, ["의원"]),
        "pharmacy": await _nearest_pharmacy(db, lat, lng),
    }


async def night_medical_density(db: AsyncSession, lat: float, lng: float, radius_m: int = 1000) -> dict:
    area_km2 = 3.141592653589793 * (radius_m / 1000) ** 2
    slots = [18, 20, 22, 24, 26, 28, 30]
    slot_counts = []
    for hour in slots:
        clinic_count = await _count_open_clinics(db, lat, lng, radius_m, hour)
        pharmacy_count = await _count_open_pharmacies(db, lat, lng, radius_m, hour)
        slot_counts.append(
            {
                "hour": _hour_label(hour),
                "count": clinic_count + pharmacy_count,
                "clinic_count": clinic_count,
                "pharmacy_count": pharmacy_count,
            }
        )

    base_count = slot_counts[0]["count"] if slot_counts else 0
    average = await db.scalar(select(func.avg(RefHealthDong.night_clinic_count)))
    return {
        "radius_m": radius_m,
        "count": base_count,
        "density": round(base_count / area_km2, 1) if area_km2 else 0.0,
        "gu_average": round(float(average), 1) if average is not None else None,
        "time_slots": slot_counts,
    }


async def hospital_access(db: AsyncSession, lat: float, lng: float, radius_m: int = 1000) -> dict:
    hospital_types = ["종합병원", "병원"]
    count_stmt = (
        select(func.count())
        .where(within_radius_expr(RefNightClinic.geom, lat, lng, radius_m))
        .where(RefNightClinic.facility_type.in_(hospital_types))
    )
    hospital_count = int(await db.scalar(count_stmt) or 0)
    nearest = await _nearest_clinic_by_types(db, lat, lng, hospital_types)
    return {
        "radius_m": radius_m,
        "hospital_count": hospital_count,
        "nearest_hospital": nearest,
    }


async def get_health_workforce(db: AsyncSession, gu_name: str | None) -> RefHealthWorkforce | None:
    if not gu_name:
        return None
    return await db.scalar(select(RefHealthWorkforce).where(RefHealthWorkforce.gu_name == gu_name))


async def health_workforce_average(db: AsyncSession) -> dict:
    row = (
        await db.execute(
            select(
                func.avg(RefHealthWorkforce.nurse_count),
                func.avg(RefHealthWorkforce.specialist_count),
                func.avg(RefHealthWorkforce.raw_score),
            )
        )
    ).one()
    nurse_avg, specialist_avg, total_avg = row
    return {
        "nurse": float(nurse_avg or 0.0),
        "specialist": float(specialist_avg or 0.0),
        "total": float(total_avg or 0.0),
    }


async def _nearest_clinic_by_types(
    db: AsyncSession,
    lat: float,
    lng: float,
    facility_types: list[str],
) -> dict | None:
    distance = distance_m_expr(RefNightClinic.geom, lat, lng).label("distance_m")
    stmt = (
        select(
            RefNightClinic.name,
            RefNightClinic.facility_type,
            RefNightClinic.address,
            RefNightClinic.close_time,
            distance,
        )
        .where(RefNightClinic.facility_type.in_(facility_types))
        .order_by(distance)
        .limit(1)
    )
    row = (await db.execute(stmt)).first()
    if row is None:
        return None
    name, facility_type, address, close_time, distance_m = row
    return {
        "name": name,
        "facility_type": facility_type,
        "address": address,
        "close_time": close_time,
        "distance_m": float(distance_m),
    }


async def _nearest_pharmacy(db: AsyncSession, lat: float, lng: float) -> dict | None:
    distance = distance_m_expr(RefPharmacy.geom, lat, lng).label("distance_m")
    stmt = (
        select(RefPharmacy.name, RefPharmacy.address, RefPharmacy.close_time, distance)
        .order_by(distance)
        .limit(1)
    )
    row = (await db.execute(stmt)).first()
    if row is None:
        return None
    name, address, close_time, distance_m = row
    return {
        "name": name,
        "facility_type": "약국",
        "address": address,
        "close_time": close_time,
        "distance_m": float(distance_m),
    }


async def _count_open_clinics(db: AsyncSession, lat: float, lng: float, radius_m: int, close_hour: int) -> int:
    stmt = (
        select(func.count())
        .where(within_radius_expr(RefNightClinic.geom, lat, lng, radius_m))
        .where(RefNightClinic.close_time >= close_hour)
    )
    return int(await db.scalar(stmt) or 0)


async def _count_open_pharmacies(db: AsyncSession, lat: float, lng: float, radius_m: int, close_hour: int) -> int:
    stmt = (
        select(func.count())
        .where(within_radius_expr(RefPharmacy.geom, lat, lng, radius_m))
        .where(RefPharmacy.close_time >= close_hour)
    )
    return int(await db.scalar(stmt) or 0)


def _hour_label(hour: int) -> str:
    if hour >= 24:
        return f"{hour - 24:02d}"
    return str(hour)
