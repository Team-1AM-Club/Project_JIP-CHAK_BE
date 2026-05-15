from pathlib import Path

import pandas as pd

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

    results["ref_subway_congestion"] = await seed_table(
        session,
        RefSubwayCongestion,
        _metro_records(base),
        replace=replace,
    )

    df = load_csv(base / "master_population_hourly_risk.csv")
    hour_cols = [col for col in df.columns if col.endswith("_인구")]
    results["ref_floating_pop"] = await seed_table(session, RefFloatingPopulation, [
        {
            "dong_code": str_or_none(row["행정동코드"]),
            "total_pop": float_or_none(row["총생활인구"]),
            "hourly_pop": {
                col.replace("_인구", ""): float_or_none(row[col])
                for col in hour_cols
            },
            "raw_score": float_or_none(row["raw_score"]),
        }
        for _, row in df.iterrows()
    ], replace=replace)

    return results


def _metro_records(base: Path) -> list[dict]:
    congestion_path = base / "master_metro_congestion.csv"
    population_path = base / "master_metro_population.csv"
    if not congestion_path.exists():
        return _legacy_subway_records(base / "master_congestion_subway.csv")

    congestion = load_csv(congestion_path)
    congestion = congestion[congestion["연도"].astype(str) == "종합"].copy()
    population = load_csv(population_path) if population_path.exists() else pd.DataFrame()
    if not population.empty:
        population = population[population["연도"].astype(str) == "종합"].copy()
        population = population[
            [
                "노선명",
                "역번호",
                "역명",
                "일평균승하차승객_종합",
                "일평균승하차승객_평일",
                "일평균승하차승객_주말",
            ]
        ]
        congestion = congestion.merge(
            population,
            on=["노선명", "역번호", "역명"],
            how="left",
        )

    return [
        {
            "line_name": str_or_none(row["노선명"]),
            "station_no": str_or_none(row["역번호"]),
            "station_name": str_or_none(row["역명"]),
            "lat": float_or_none(row["위도"]),
            "lon": float_or_none(row["경도"]),
            "geom": make_point(row["경도"], row["위도"]),
            "avg_congestion_total": float_or_none(row["일평균혼잡도_종합"]),
            "avg_congestion_weekday": float_or_none(row["일평균혼잡도_평일"]),
            "avg_congestion_weekend": float_or_none(row["일평균혼잡도_주말"]),
            "peak_congestion_total": float_or_none(row["피크시간혼잡도_전체"]),
            "peak_congestion_weekday": float_or_none(row["피크시간혼잡도_평일"]),
            "peak_congestion_weekend": float_or_none(row["피크시간혼잡도_주말"]),
            "daily_passengers_total": float_or_none(row.get("일평균승하차승객_종합")),
            "daily_passengers_weekday": float_or_none(row.get("일평균승하차승객_평일")),
            "daily_passengers_weekend": float_or_none(row.get("일평균승하차승객_주말")),
            "peak_max_congestion": float_or_none(row["피크시간혼잡도_전체"]),
            "raw_score": float_or_none(row["피크시간혼잡도_전체"]),
        }
        for _, row in congestion.iterrows()
    ]


def _legacy_subway_records(path: Path) -> list[dict]:
    df = load_csv(path)
    return [
        {
            "station_name": str_or_none(row["출발역"]),
            "peak_max_congestion": float_or_none(row["peak_max_congestion"]),
            "raw_score": float_or_none(row["raw_score_sub_cong"]),
        }
        for _, row in df.iterrows()
    ]
