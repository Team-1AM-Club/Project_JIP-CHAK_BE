from typing import Protocol

from app.core.config import settings
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
            "flood_map": {"in_flood_trace": False},
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
            police_pop = await security_repo.get_police_pop_score(db, gu_name)
            safepath = await security_repo.get_safepath_score(db, dong_code)

            in_flood_trace = await flood_repo.is_in_flood_trace(db, lat, lng)
            pump_cap = await flood_repo.nearest_pump_capacity(db, lat, lng)
            impervious_ratio = await flood_repo.get_impervious_ratio(db, gu_name)

            nearby_noise_pubs = await noise_repo.count_nearby_pubs(db, lat, lng)
            noise_complaint = await noise_repo.get_noise_complaint(db, gu_name)
            nearest_noise_db = await noise_repo.get_nearest_idw_noise(db, lat, lng)
            avg_noise_db = await noise_repo.get_avg_noise_measurement(db)
            road_noise = await noise_repo.get_road_noise_score(db, gu_name)
            traffic_noise = await noise_repo.get_nearest_traffic_noise(db, lat, lng)
            lden_noise = await noise_repo.get_nearest_lden_noise(db, lat, lng)
            aircraft_noise = await noise_repo.get_avg_aircraft_noise(db)
            rail_noise = await noise_repo.get_avg_rail_noise(db)
            hourly_noise = await noise_repo.get_avg_hourly_noise(db)

            nightopen_count = await medical_repo.count_nearby_clinics(db, lat, lng)
            pharmacy_count = await medical_repo.count_nearby_pharmacies(db, lat, lng)
            workforce = await medical_repo.get_health_workforce(db, gu_name)

            bus_congestion = await congestion_repo.avg_nearby_bus_congestion(db, lat, lng)
            floating_pop = await congestion_repo.get_floating_pop(db, dong_code)
            commute_congestion = await congestion_repo.get_avg_subway_congestion(db)

        crime_value = crime.raw_score if crime and crime.raw_score is not None else 0.0
        impervious_value = impervious_ratio if impervious_ratio is not None else 0.0
        pump_value = pump_cap if pump_cap is not None else 0.0
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
            "safety_map": None,
            "impervious_ratio": float(impervious_value),
            "pump_cap": float(pump_value),
            "flood_map": {"in_flood_trace": in_flood_trace},
            "noise_pub_density": float(nearby_noise_pubs or 0.0),
            "noise_complaint": float(noise_complaint_value),
            "noise_db": float(noise_db_value),
            "road_noise": float(road_noise_value),
            "aircraft_noise": float(aircraft_noise_value),
            "rail_noise": float(rail_noise_value),
            "noise_hourly": float(hourly_noise_value),
            "noise_table": None,
            "night_clinic": float(nightopen_count or 0.0),
            "pharmacy_count": float(pharmacy_count or 0.0),
            "medical_staff": float(workforce_value),
            "medic_map": None,
            "congestion_data": {
                "hourly_population_density": floating_pop,
                "bus_congestion": bus_congestion,
                "commute_congestion": commute_congestion,
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

def _create_client() -> PublicDataClient:
    if settings.DATA_PROVIDER.lower() == "db":
        return DbPublicDataClient()
    return MockPublicDataClient()

public_data_client: PublicDataClient = _create_client()
