# 불완전: 실제 공공데이터 소스 확정 전까지 Protocol과 Mock 구현만 제공함.
from typing import Protocol


class PublicDataClient(Protocol):
    async def fetch_analysis_data(self, lat: float, lng: float, dong_code: str) -> dict:
        ...


class MockPublicDataClient:
    async def fetch_analysis_data(self, lat: float, lng: float, dong_code: str) -> dict:
        return {
            "criminal_occur": [12, 8, 3, 4, 1],
            "cctv_count": 15,
            "lamp_count": 45,
            "police_dist": 850,
            "altitude": 22.5,
            "flood_hist": 0,
            "low_ratio": 12,
            "pump_cap": 70,
            "river_dist": 900,
            "road_noise": 58,
            "noise_report": 3,
            "ent_place": 4,
            "train_noise": 0,
            "medic_dist": 420,
            "nightopen_count": 4,
            "emeropen_count": 1,
            "emer_cap": 20,
            "doctor_ratio": 3.2,
            "congestion_data": {"peak_index": 35},
        }


public_data_client: PublicDataClient = MockPublicDataClient()
