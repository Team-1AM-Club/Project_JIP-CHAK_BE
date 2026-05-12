from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from sqlalchemy import func, select

from app.db.session import AsyncSessionLocal
from app.models.reference.congestion import RefBusHourly, RefBusStop, RefFloatingPopulation, RefSubwayCongestion
from app.models.reference.flood import RefFloodPump, RefFloodTrace, RefImpervious
from app.models.reference.medical import RefHealthDong, RefHealthWorkforce, RefNightClinic, RefPharmacy
from app.models.reference.noise import (
    RefNoiseAircraft,
    RefNoiseComplaint,
    RefNoiseHourly,
    RefNoiseMeasurement,
    RefNoisePub,
    RefNoiseRail,
    RefNoiseRoad,
)
from app.models.reference.security import (
    RefCctv,
    RefCctvGrowth,
    RefCrime,
    RefLightBlind,
    RefPolice,
    RefPolicePopulation,
    RefSafePath,
)
from scripts.seeders.common import load_csv


TABLES = {
    "ref_cctv": (RefCctv, "치안리스크/master_security_cctv.csv"),
    "ref_light_blind": (RefLightBlind, "치안리스크/master_security_light_blind.csv"),
    "ref_police": (RefPolice, "치안리스크/master_security_police.csv"),
    "ref_crime": (RefCrime, "치안리스크/master_security_crime.csv"),
    "ref_police_pop": (RefPolicePopulation, "치안리스크/master_security_police_pop.csv"),
    "ref_cctv_growth": (RefCctvGrowth, "치안리스크/master_security_cctv_growth.csv"),
    "ref_safepath": (RefSafePath, "치안리스크/master_security_safepath.csv"),
    "ref_flood_trace": (RefFloodTrace, "침수리스크/master_flood_trace.geojson"),
    "ref_flood_pump": (RefFloodPump, "침수리스크/master_flood_pump.csv"),
    "ref_impervious": (RefImpervious, "침수리스크/master_flood_impervious.csv"),
    "ref_noise_pub": (RefNoisePub, "소음리스크/master_noise_pub_converted.csv"),
    "ref_noise_road": (RefNoiseRoad, "소음리스크/master_noise_road.csv"),
    "ref_noise_rail": (RefNoiseRail, "소음리스크/master_noise_rail.csv"),
    "ref_noise_complaint": (RefNoiseComplaint, "소음리스크/master_noise_complaint.csv"),
    "ref_noise_measurement": (RefNoiseMeasurement, "소음리스크/master_noise_measurement.csv"),
    "ref_noise_aircraft": (RefNoiseAircraft, "소음리스크/master_noise_aircraft.csv"),
    "ref_noise_hourly": (RefNoiseHourly, "소음리스크/master_noise_hourly_estimation.csv"),
    "ref_night_clinic": (RefNightClinic, "의료접근성/master_map_night_clinics_point.csv"),
    "ref_pharmacy": (RefPharmacy, "의료접근성/master_map_pharmacy_point_converted.csv"),
    "ref_health_dong": (RefHealthDong, "의료접근성/master_health_facilities_dong.csv"),
    "ref_health_workforce": (RefHealthWorkforce, "의료접근성/master_health_workforce_gu.csv"),
    "ref_bus_stop": (RefBusStop, "생활혼잡도/master_congestion_bus.csv"),
    "ref_bus_hourly": (RefBusHourly, "생활혼잡도/master_congestion_bus.csv"),
    "ref_subway_congestion": (RefSubwayCongestion, "생활혼잡도/master_congestion_subway.csv"),
    "ref_floating_pop": (RefFloatingPopulation, "생활혼잡도/master_congestion_population.csv"),
}


async def db_count(model) -> int:
    async with AsyncSessionLocal() as session:
        return int(await session.scalar(select(func.count()).select_from(model)) or 0)


def source_count(data_dir: Path, relative_path: str) -> int | None:
    path = data_dir / relative_path
    if not path.exists():
        return None
    if path.suffix == ".geojson":
        with open(path, encoding="utf-8") as f:
            return len(json.load(f).get("features", []))
    df = load_csv(path)
    if path.name in {"master_noise_pub_converted.csv", "master_map_pharmacy_point_converted.csv"}:
        df = df.dropna(subset=["경도", "위도"])
    return len(df)


async def run(data_dir: Path) -> None:
    for table_name, (model, relative_path) in TABLES.items():
        expected = source_count(data_dir, relative_path)
        actual = await db_count(model)
        status = "OK" if expected == actual else "CHECK"
        print(f"{table_name:<26} source={expected!s:<8} db={actual:<8} {status}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare source file counts with ref_* table counts.")
    parser.add_argument("--data-dir", type=Path, default=Path(os.getenv("DATA_DIR", "data")))
    args = parser.parse_args()
    asyncio.run(run(args.data_dir))


if __name__ == "__main__":
    main()
