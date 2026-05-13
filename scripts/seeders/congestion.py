from pathlib import Path

from app.models.reference.congestion import (
    RefBusHourly,
    RefBusStop,
    RefFloatingPopulation,
    RefSubwayCongestion,
)
from scripts.seeders.common import float_or_none, load_csv, make_point, seed_table, str_or_none


async def seed_congestion(session, data_dir: Path, *, replace: bool = False) -> dict[str, int]:
    base = data_dir / "생활혼잡도"
    results: dict[str, int] = {}

    df = load_csv(base / "master_congestion_bus.csv")
    results["ref_bus_stop"] = await seed_table(session, RefBusStop, [
        {
            "node_id": str_or_none(row["NODE_ID"]),
            "ars_id": str_or_none(row["ARS_ID"]),
            "stop_name": str_or_none(row["정류소명"]),
            "stop_type": str_or_none(row.get("정류소타입") or row.get("속성")),
            "lat": float(row["Y좌표"]),
            "lon": float(row["X좌표"]),
            "geom": make_point(row["X좌표"], row["Y좌표"]),
            "daily_avg_usage": float_or_none(row["daily_avg_usage"]),
            "raw_score": float_or_none(row["raw_score_bus_cong"]),
        }
        for _, row in df.iterrows()
    ], replace=replace)

    df_hourly = load_csv(base / "master_bus_hourly_per_stop.csv")
    hour_cols = [col for col in df_hourly.columns if col.endswith("_유동인구")]
    results["ref_bus_hourly"] = await seed_table(session, RefBusHourly, [
        {
            "node_id": str_or_none(row["NODE_ID"]),
            "stop_name": str_or_none(row["정류소명"]),
            "lat": float(row["Y좌표"]),
            "lon": float(row["X좌표"]),
            "geom": make_point(row["X좌표"], row["Y좌표"]),
            "hourly_pop": {
                col.replace("_유동인구", ""): float_or_none(row[col])
                for col in hour_cols
            },
        }
        for _, row in df_hourly.iterrows()
    ], replace=replace)

    df = load_csv(base / "master_congestion_subway.csv")
    results["ref_subway_congestion"] = await seed_table(session, RefSubwayCongestion, [
        {
            "station_name": str_or_none(row["출발역"]),
            "peak_max_congestion": float_or_none(row["peak_max_congestion"]),
            "raw_score": float_or_none(row["raw_score_sub_cong"]),
        }
        for _, row in df.iterrows()
    ], replace=replace)

    df = load_csv(base / "preprocessed_population_risk.csv")
    results["ref_floating_pop"] = await seed_table(session, RefFloatingPopulation, [
        {
            "dong_code": str_or_none(row["행정동코드"]),
            "total_pop": float_or_none(row["총생활인구"]),
            "raw_score": float_or_none(row["raw_score"]),
        }
        for _, row in df.iterrows()
    ], replace=replace)

    return results
