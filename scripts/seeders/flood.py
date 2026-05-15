from pathlib import Path
from typing import Any

import pandas as pd

from app.models.reference.flood import (
    RefFloodDefense,
    RefFloodTracePoint,
    RefFloodTraceSummary,
)
from scripts.seeders.common import float_or_none, int_or_none, load_csv, make_point, seed_table, str_or_none


async def seed_flood(session, data_dir: Path, *, replace: bool = False) -> dict[str, int]:
    base = data_dir / "침수리스크"
    results: dict[str, int] = {}

    defense_df = load_csv(base / "master_flood_defense.csv")
    results["ref_flood_defense"] = await seed_table(
        session,
        RefFloodDefense,
        [
            {
                "gu_name": str_or_none(row["자치구"]),
                "avg_elevation_m": float_or_none(row["avg_elevation_m"]),
                "num_stations": float_or_none(row["num_stations"]),
                "total_pump_m3": float_or_none(row["total_pump_m3"]),
                "total_basin": float_or_none(row["total_basin"]),
                "pump_efficiency": float_or_none(row["pump_efficiency"]),
                "max_freq": float_or_none(row["max_freq"]),
                "avg_coverage_rate": float_or_none(row["avg_coverage_rate"]),
                "imperv_proxy": float_or_none(row["imperv_proxy"]),
                "n_buildings": int_or_none(row["n_buildings"]),
                "score_elevation": float_or_none(row["score_elevation"]),
                "score_pump": float_or_none(row["score_pump"]),
                "score_imperv": float_or_none(row["score_imperv"]),
                "raw_score": float_or_none(row["raw_score_flood_defense"]),
                "contour_line_count": int_or_none(row["contour_line_count"]),
                "score_contour": float_or_none(row["score_contour"]),
            }
            for _, row in defense_df.iterrows()
        ],
        replace=replace,
    )

    trace_df = load_csv(base / "master_flood_trace.csv")
    results["ref_flood_trace_summary"] = await seed_table(
        session,
        RefFloodTraceSummary,
        [
            {
                "gu_name": str_or_none(row["자치구"]),
                "flood_count": float_or_none(row["flood_count"]),
                "total_flood_area": float_or_none(row["total_flood_area"]),
                "mean_flood_area": float_or_none(row["mean_flood_area"]),
                "mean_flood_depth": float_or_none(row["mean_flood_depth"]),
                "max_flood_depth": float_or_none(row["max_flood_depth"]),
                "raw_score": float_or_none(row["raw_score_flood_trace"]),
                "data_available": bool_or_none(row["data_available"]),
                "data_year": int_or_none(row["data_year"]),
            }
            for _, row in trace_df.iterrows()
        ],
        replace=replace,
    )

    point_df = load_csv(base / "master_flood_trace_points.csv")
    results["ref_flood_trace_point"] = await seed_table(
        session,
        RefFloodTracePoint,
        [
            {
                "gu_name": str_or_none(row["자치구"]),
                "address": str_or_none(row["피해위치"]),
                "flood_year": int_or_none(row["flood_year"]),
                "flood_area_m2": float_or_none(row["flood_area_m2"]),
                "flood_depth_cm": float_or_none(row["flood_depth_cm"]),
                "flood_type": str_or_none(row["flood_type"]),
                "lat": float_or_none(row["lat"]),
                "lon": float_or_none(row["lon"]),
                "geom": make_point(row["lon"], row["lat"]),
                "is_outlier_area": bool_or_none(row["is_outlier_area"]),
                "flood_area_m2_clipped": float_or_none(row["flood_area_m2_clipped"]),
                "raw_score": float_or_none(row["raw_score_flood_point"]),
            }
            for _, row in point_df.iterrows()
        ],
        replace=replace,
    )

    return results


def bool_or_none(value: Any) -> bool | None:
    if pd.isna(value):
        return None
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"true", "1", "yes", "y"}
