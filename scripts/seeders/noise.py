from pathlib import Path

from app.models.reference.noise import (
    RefNoiseAircraft,
    RefNoiseComplaint,
    RefNoiseHourly,
    RefNoiseMeasurement,
    RefNoisePub,
    RefNoiseRail,
    RefNoiseRoad,
)
from scripts.seeders.common import float_or_none, load_csv, make_point, seed_table, str_or_none


async def seed_noise(session, data_dir: Path, *, replace: bool = False) -> dict[str, int]:
    base = data_dir / "소음리스크"
    results: dict[str, int] = {}

    df = load_csv(base / "master_noise_pub_converted.csv")
    results["ref_noise_pub"] = await seed_table(session, RefNoisePub, [
        {
            "name": str_or_none(row["사업장명"]),
            "address": str_or_none(row["도로명주소"]),
            "lat": float(row["위도"]),
            "lon": float(row["경도"]),
            "geom": make_point(row["경도"], row["위도"]),
            "raw_score": float_or_none(row["raw_score_noise_pub"]),
        }
        for _, row in df.iterrows()
    ], replace=replace)

    df = load_csv(base / "master_noise_road.csv")
    results["ref_noise_road"] = await seed_table(session, RefNoiseRoad, [
        {
            "its_link_id": str_or_none(row["ITS LINK ID"]),
            "road_name": str_or_none(row["도로명"]),
            "region": str_or_none(row["권역"]),
            "raw_score": float_or_none(row["raw_score_road_noise"]),
        }
        for _, row in df.iterrows()
    ], replace=replace)

    df = load_csv(base / "master_noise_rail.csv")
    results["ref_noise_rail"] = await seed_table(session, RefNoiseRail, [
        {
            "from_station": str_or_none(row["출발_역_명칭"]),
            "from_line": str_or_none(row["출발_호선_내용"]),
            "to_station": str_or_none(row["도착_역_명칭"]),
            "to_line": str_or_none(row["도착_호선_내용"]),
            "distance": float_or_none(row["거리"]),
            "raw_score": float_or_none(row["raw_score_rail_noise"]),
        }
        for _, row in df.iterrows()
    ], replace=replace)

    df = load_csv(base / "master_noise_complaint.csv")
    results["ref_noise_complaint"] = await seed_table(session, RefNoiseComplaint, [
        {"gu_name": str_or_none(row["자치구명"]), "raw_score": float_or_none(row["raw_score_noise_complaint"])}
        for _, row in df.iterrows()
    ], replace=replace)

    df = load_csv(base / "master_noise_measurement.csv")
    results["ref_noise_measurement"] = await seed_table(session, RefNoiseMeasurement, [
        {
            "station": str_or_none(row["측정지점"]),
            "address": str_or_none(row["주소"]),
            "land_use": str_or_none(row["용도구분"]),
            "leq": float_or_none(row["LEQ"]),
            "raw_score": float_or_none(row["raw_score_noise_db"]),
        }
        for _, row in df.iterrows()
    ], replace=replace)

    df = load_csv(base / "master_noise_aircraft.csv")
    results["ref_noise_aircraft"] = await seed_table(session, RefNoiseAircraft, [
        {"station": str_or_none(row["측정지점"]), "raw_score": float_or_none(row["raw_score_aircraft"])}
        for _, row in df.iterrows()
    ], replace=replace)

    df = load_csv(base / "master_noise_hourly_estimation.csv")
    results["ref_noise_hourly"] = await seed_table(session, RefNoiseHourly, [
        {
            "station": str_or_none(row["측정지점"]),
            "hour": str_or_none(row["시간"]),
            "raw_score": float_or_none(row["raw_score_noise_hourly"]),
        }
        for _, row in df.iterrows()
    ], replace=replace)

    return results
