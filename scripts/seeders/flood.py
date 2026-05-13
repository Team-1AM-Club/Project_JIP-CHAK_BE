import json
from pathlib import Path

from geoalchemy2.shape import from_shape
from shapely.geometry import shape

from app.models.reference.flood import RefFloodPump, RefFloodTrace, RefImpervious
from scripts.seeders.common import float_or_none, load_csv, make_point, seed_table, str_or_none


async def seed_flood(session, data_dir: Path, *, replace: bool = False) -> dict[str, int]:
    base = data_dir / "침수리스크"
    results: dict[str, int] = {}

    with open(base / "master_flood_trace.geojson", encoding="utf-8") as f:
        geojson = json.load(f)
    results["ref_flood_trace"] = await seed_table(session, RefFloodTrace, [
        {
            "geom": from_shape(shape(feature["geometry"]), srid=4326),
            "properties": feature.get("properties", {}),
        }
        for feature in geojson.get("features", [])
    ], replace=replace)

    df = load_csv(base / "master_flood_pump.csv")
    results["ref_flood_pump"] = await seed_table(session, RefFloodPump, [
        {
            "name": str_or_none(row["시설물명"]),
            "address": str_or_none(row["상세주소"]),
            "max_capacity": float_or_none(row["배수장_최대배수량"]),
            "lat": float(row["lat"]),
            "lon": float(row["lon"]),
            "geom": make_point(row["lon"], row["lat"]),
            "raw_score": float_or_none(row["raw_score_pump"]),
        }
        for _, row in df.iterrows()
    ], replace=replace)

    df = load_csv(base / "master_flood_impervious.csv")
    results["ref_impervious"] = await seed_table(session, RefImpervious, [
        {
            "gu_name": str_or_none(row["자치구명"]),
            "impervious_ratio": float_or_none(row["불투수면적률"]),
            "raw_score": float_or_none(row["raw_score_impervious"]),
        }
        for _, row in df.iterrows()
    ], replace=replace)

    return results
