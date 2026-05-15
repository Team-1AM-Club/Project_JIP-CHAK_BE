from typing import Protocol

from app.core.config import settings
from app.core.meta_stats import get_stat
from app.db.session import AsyncSessionLocal
from app.repositories import (
    congestion_repo,
    flood_repo,
    medical_repo,
    noise_repo,
    security_repo,
)

GU_CODE_MAP = {
    "11110": "종로구",
    "11140": "중구",
    "11170": "용산구",
    "11200": "성동구",
    "11215": "광진구",
    "11230": "동대문구",
    "11260": "중랑구",
    "11290": "성북구",
    "11305": "강북구",
    "11320": "도봉구",
    "11350": "노원구",
    "11380": "은평구",
    "11410": "서대문구",
    "11440": "마포구",
    "11470": "양천구",
    "11500": "강서구",
    "11530": "구로구",
    "11545": "금천구",
    "11560": "영등포구",
    "11590": "동작구",
    "11620": "관악구",
    "11650": "서초구",
    "11680": "강남구",
    "11710": "송파구",
    "11740": "강동구",
}

class PublicDataClient(Protocol):
    async def fetch_analysis_data(self, lat: float, lng: float, dong_code: str, address: str | None = None) -> dict:
        ...

class MockPublicDataClient:
    async def fetch_analysis_data(self, lat: float, lng: float, dong_code: str, address: str | None = None) -> dict:
        return {
            "cctv_count": 15.0,
            "cctv_growth": 200.0,
            "crime_count": 3000.0,
            "safepath_score": 1000.0,
            "police_count": 30.0,
            "police_pop_ratio": 0.002,
            "light_blind_ratio": 10.0,
            "safety_map": None,
            "impervious_ratio": 50.0,
            "pump_cap": 70.0,
            "flood_map": {
                "in_flood_trace": False,
                "flood_defense": None,
                "flood_history": None,
            },
            "noise_pub_density": 50.0,
            "noise_complaint": 2000.0,
            "noise_db": 70.0,
            "road_noise": 20000.0,
            "aircraft_noise": 65.0,
            "rail_noise": 0.5,
            "noise_hourly": 65.0,
            "noise_table": None,
            "night_clinic": 10.0,
            "pharmacy_count": 15.0,
            "medical_staff": 3000.0,
            "medic_map": None,
            "congestion_data": {"peak_index": 35},
        }

class DbPublicDataClient:
    async def fetch_analysis_data(self, lat: float, lng: float, dong_code: str, address: str | None = None) -> dict:
        gu_name = _extract_gu_name(dong_code, address)

        async with AsyncSessionLocal() as db:
            cctv_count = await security_repo.count_nearby_cctv(db, lat, lng)
            light_score = await security_repo.avg_light_blind_score(db, lat, lng)
            crime = await security_repo.get_crime_score(db, gu_name)
            cctv_growth = await security_repo.get_cctv_growth_score(db, gu_name)
            police_score = await security_repo.get_police_score_nearby(db, lat, lng, gu_name)
            nearest_police = await security_repo.nearest_police_detail(db, lat, lng)
            police_pop = await security_repo.get_police_pop_score(db, gu_name)
            safepath = await security_repo.get_safepath_score(db, dong_code)
            light_stats = await security_repo.light_stats_nearby(db, lat, lng)

            flood_defense = await flood_repo.get_flood_defense(db, gu_name)
            flood_defense_avg = await flood_repo.get_flood_defense_average_score(db)
            flood_defense_top_percent = await flood_repo.get_flood_defense_top_percent(db, gu_name)
            flood_trace_summary = await flood_repo.get_flood_trace_summary(db, gu_name)
            flood_trace_avg_count = await flood_repo.get_flood_trace_average_count(db)
            flood_trace_years = await flood_repo.get_flood_trace_year_counts(db, gu_name)
            flood_trace_events = await flood_repo.get_flood_trace_events(db, gu_name)
            nearby_flood_trace_count = await flood_repo.count_nearby_flood_trace_points(db, lat, lng)

            nearby_noise_pubs = await noise_repo.count_nearby_pubs(db, lat, lng, radius_m=200)
            noise_complaint = await noise_repo.get_noise_complaint(db, gu_name)
            avg_noise_complaint = await noise_repo.get_avg_noise_complaint(db)
            nearest_noise_db = await noise_repo.get_nearest_idw_noise(db, lat, lng)
            avg_noise_db = await noise_repo.get_avg_noise_measurement(db)
            road_noise = await noise_repo.get_road_noise_score(db, gu_name)
            traffic_noise = await noise_repo.get_nearest_traffic_noise(db, lat, lng)
            traffic_noise_detail = await noise_repo.get_nearest_traffic_noise_detail(db, lat, lng)
            lden_noise = await noise_repo.get_nearest_lden_noise(db, lat, lng)
            measurement_detail = await noise_repo.get_nearest_measurement_detail(db, lat, lng)
            hourly_noise_rows = await noise_repo.get_hourly_noise_by_station(
                db,
                measurement_detail.get("station") if measurement_detail else None,
            )
            aircraft_noise = await noise_repo.get_avg_aircraft_noise(db)
            rail_noise = await noise_repo.get_avg_rail_noise(db)
            hourly_noise = await noise_repo.get_avg_hourly_noise(db)

            nightopen_count = await medical_repo.count_nearby_clinics(db, lat, lng)
            pharmacy_count = await medical_repo.count_nearby_pharmacies(db, lat, lng)
            workforce = await medical_repo.get_health_workforce(db, gu_name)
            nearest_medical = await medical_repo.nearest_medical_facilities(db, lat, lng)
            night_density = await medical_repo.night_medical_density(db, lat, lng)
            hospital_access = await medical_repo.hospital_access(db, lat, lng)
            workforce_average = await medical_repo.health_workforce_average(db)

            bus_congestion = await congestion_repo.avg_nearby_bus_congestion(db, lat, lng)
            floating_pop = await congestion_repo.get_floating_pop(db, dong_code)
            commute_congestion = await congestion_repo.get_avg_subway_congestion(db)
            population_detail = await congestion_repo.get_floating_population_detail(db, dong_code)
            nearest_subway = await congestion_repo.nearest_subway_station(db, lat, lng)
            nearest_bus = await congestion_repo.nearest_bus_stop(db, lat, lng)
            bus_hourly = await congestion_repo.nearby_bus_hourly_average(db, lat, lng)

        crime_value = crime.raw_score if crime and crime.raw_score is not None else 0.0
        impervious_value = (
            flood_defense.imperv_proxy
            if flood_defense is not None and flood_defense.imperv_proxy is not None
            else 0.0
        )
        pump_value = (
            flood_defense.pump_efficiency
            if flood_defense is not None and flood_defense.pump_efficiency is not None
            else 0.0
        )
        noise_db_value = nearest_noise_db if nearest_noise_db is not None else avg_noise_db
        noise_db_value = noise_db_value if noise_db_value is not None else 0.0
        workforce_value = workforce.raw_score if workforce and workforce.raw_score is not None else 0.0
        light_value = light_score if light_score is not None else 0.0
        cctv_growth_value = cctv_growth.raw_score if cctv_growth and cctv_growth.raw_score is not None else 0.0
        police_value = police_score if police_score is not None else 0.0
        safepath_value = safepath.raw_score if safepath and safepath.raw_score is not None else 0.0
        police_pop_value = police_pop.raw_score if police_pop and police_pop.raw_score is not None else 0.0
        noise_complaint_value = noise_complaint.raw_score if noise_complaint and noise_complaint.raw_score is not None else 0.0
        road_noise_value = traffic_noise if traffic_noise is not None else road_noise
        road_noise_value = road_noise_value if road_noise_value is not None else 0.0
        aircraft_noise_value = aircraft_noise if aircraft_noise is not None else 0.0
        rail_noise_value = rail_noise if rail_noise is not None else 0.0
        hourly_noise_value = lden_noise if lden_noise is not None else hourly_noise
        hourly_noise_value = hourly_noise_value if hourly_noise_value is not None else 0.0

        return {
            "cctv_count": float(cctv_count or 0.0),
            "cctv_growth": float(cctv_growth_value),
            "crime_count": float(crime_value),
            "safepath_score": float(safepath_value),
            "police_count": float(police_value),
            "police_pop_ratio": float(police_pop_value),
            "light_blind_ratio": float(light_value),
            "safety_map": _safety_map(
                crime=crime,
                cctv_growth=cctv_growth,
                nearest_police=nearest_police,
                light_stats=light_stats,
                cctv_count=float(cctv_count or 0.0),
                light_score=light_value,
                safepath_value=safepath_value,
                gu_name=gu_name,
                address=address,
            ),
            "impervious_ratio": float(impervious_value),
            "pump_cap": float(pump_value),
            "flood_map": _flood_map(
                defense=flood_defense,
                defense_average_score=flood_defense_avg,
                defense_top_percent=flood_defense_top_percent,
                trace_summary=flood_trace_summary,
                trace_average_count=flood_trace_avg_count,
                trace_years=flood_trace_years,
                trace_events=flood_trace_events,
                nearby_trace_count=nearby_flood_trace_count,
            ),
            "noise_pub_density": float(nearby_noise_pubs or 0.0),
            "noise_complaint": float(noise_complaint_value),
            "noise_db": float(noise_db_value),
            "road_noise": float(road_noise_value),
            "aircraft_noise": float(aircraft_noise_value),
            "rail_noise": float(rail_noise_value),
            "noise_hourly": float(hourly_noise_value),
            "noise_table": _noise_table(
                gu_name=gu_name,
                pub_count=nearby_noise_pubs,
                pub_radius_m=200,
                complaint=noise_complaint,
                avg_complaint=avg_noise_complaint,
                traffic=traffic_noise_detail,
                measurement=measurement_detail,
                hourly_rows=hourly_noise_rows,
                nearest_noise_db=noise_db_value,
            ),
            "night_clinic": float(nightopen_count or 0.0),
            "pharmacy_count": float(pharmacy_count or 0.0),
            "medical_staff": float(workforce_value),
            "medic_map": _medic_map(
                nearest_medical=nearest_medical,
                night_density=night_density,
                hospital_access=hospital_access,
                workforce=workforce,
                workforce_average=workforce_average,
                gu_name=gu_name,
            ),
            "congestion_data": {
                "hourly_population_density": floating_pop,
                "bus_congestion": bus_congestion,
                "commute_congestion": (
                    nearest_subway.get("peak_congestion_total")
                    if nearest_subway and nearest_subway.get("peak_congestion_total") is not None
                    else commute_congestion
                ),
                "population_detail": population_detail,
                "nearest_subway": nearest_subway,
                "nearest_bus": nearest_bus,
                "bus_hourly": bus_hourly,
            },
        }

def _extract_gu_name(dong_code: str, address: str | None = None) -> str | None:
    if dong_code:
        gu_name = GU_CODE_MAP.get(str(dong_code)[:5])
        if gu_name:
            return gu_name
    if address:
        for gu in GU_CODE_MAP.values():
            if gu in address:
                return gu
    return None


def _safety_map(
    *,
    crime,
    cctv_growth,
    nearest_police: dict | None,
    light_stats: dict,
    cctv_count: float,
    light_score: float,
    safepath_value: float,
    gu_name: str | None,
    address: str | None,
) -> dict:
    return {
        "gu_name": gu_name,
        "display_region_name": _display_region_name(address, gu_name),
        "crime_detail": crime.detail_json if crime is not None else None,
        "cctv_growth_detail": cctv_growth.detail_json if cctv_growth is not None else None,
        "nearest_police": nearest_police,
        "street_light": {
            **light_stats,
            "score": light_score,
        },
        "cctv": {
            "nearby_count": round(cctv_count),
            "radius_m": 500,
        },
        "safepath": {
            "score": safepath_value,
        },
    }


def _medic_map(
    *,
    nearest_medical: dict,
    night_density: dict,
    hospital_access: dict,
    workforce,
    workforce_average: dict,
    gu_name: str | None,
) -> dict:
    return {
        "gu_name": gu_name,
        "nearest_medical": nearest_medical,
        "night_density": night_density,
        "hospital_access": hospital_access,
        "workforce": None if workforce is None else {
            "gu_name": workforce.gu_name,
            "nurse_count": workforce.nurse_count,
            "specialist_count": workforce.specialist_count,
            "total": workforce.raw_score,
        },
        "workforce_average": workforce_average,
    }


def _flood_map(
    *,
    defense,
    defense_average_score: float | None,
    defense_top_percent: int | None,
    trace_summary,
    trace_average_count: float | None,
    trace_years: list[dict],
    trace_events: list[dict],
    nearby_trace_count: int,
) -> dict:
    defense_score = _normalize_score("flood_defense", defense.raw_score if defense is not None else None)
    trace_count = _float_or_zero(trace_summary.flood_count if trace_summary is not None else None)
    return {
        "in_flood_trace": nearby_trace_count > 0,
        "nearby_trace_count": nearby_trace_count,
        "flood_defense": None if defense is None else {
            "gu_name": defense.gu_name,
            "score": defense_score,
            "gu_average": defense_average_score,
            "top_percent": defense_top_percent,
            "avg_elevation_m": _float_or_none(defense.avg_elevation_m),
            "num_stations": _float_or_none(defense.num_stations),
            "total_pump_m3": _float_or_none(defense.total_pump_m3),
            "pump_efficiency": _float_or_none(defense.pump_efficiency),
            "imperv_proxy": _float_or_none(defense.imperv_proxy),
            "score_elevation": _ratio_to_score(defense.score_elevation),
            "score_pump": _ratio_to_score(defense.score_pump),
            "score_imperv": _ratio_to_score(defense.score_imperv),
            "contour_line_count": defense.contour_line_count,
            "score_contour": _ratio_to_score(defense.score_contour),
        },
        "flood_history": None if trace_summary is None else {
            "period": _history_period(trace_summary.data_year),
            "total_count": round(trace_count),
            "gu_average": trace_average_count,
            "data_available": bool(trace_summary.data_available),
            "total_flood_area": _float_or_none(trace_summary.total_flood_area),
            "mean_flood_area": _float_or_none(trace_summary.mean_flood_area),
            "mean_flood_depth": _float_or_none(trace_summary.mean_flood_depth),
            "max_flood_depth": _float_or_none(trace_summary.max_flood_depth),
            "raw_score": _float_or_none(trace_summary.raw_score),
            "data_year": trace_summary.data_year,
            "years": trace_years,
            "events": trace_events,
        },
    }


def _noise_table(
    *,
    gu_name: str | None,
    pub_count: int,
    pub_radius_m: int,
    complaint,
    avg_complaint: float | None,
    traffic: dict | None,
    measurement: dict | None,
    hourly_rows: list[dict],
    nearest_noise_db: float | None,
) -> dict:
    return {
        "pub": {
            "count": int(pub_count or 0),
            "radius_m": pub_radius_m,
        },
        "complaint": {
            "gu_name": gu_name,
            "yearly_count": _float_or_none(complaint.raw_score if complaint else None),
            "seoul_average_yearly": _float_or_none(avg_complaint),
        },
        "traffic": traffic,
        "measurement": measurement,
        "hourly": hourly_rows,
        "nearest_noise_db": _float_or_none(nearest_noise_db),
    }


def _float_or_none(value) -> float | None:
    return float(value) if value is not None else None


def _float_or_zero(value) -> float:
    return float(value) if value is not None else 0.0


def _ratio_to_score(value) -> int | None:
    if value is None:
        return None
    return max(0, min(100, round(float(value) * 100)))


def _normalize_score(key: str, value) -> int | None:
    if value is None:
        return None
    stat = get_stat(key)
    if not stat or stat["p95"] == stat["p05"]:
        return _ratio_to_score(value)
    score = (float(value) - stat["p05"]) / (stat["p95"] - stat["p05"]) * 100
    return max(0, min(100, round(score)))


def _history_period(data_year: int | None) -> str:
    return str(data_year or 2025)


def _display_region_name(address: str | None, gu_name: str | None) -> str | None:
    if address:
        parts = address.split()
        for part in parts:
            if part.endswith("동"):
                return f"{part} 기준"
        if len(parts) >= 3:
            return f"{parts[2]} 기준"
    return f"{gu_name} 기준" if gu_name else None

def _create_client() -> PublicDataClient:
    if settings.DATA_PROVIDER.lower() == "db":
        return DbPublicDataClient()
    return MockPublicDataClient()

public_data_client: PublicDataClient = _create_client()
