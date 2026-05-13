from pathlib import Path

from app.models.reference.security import (
    RefCctv,
    RefCctvGrowth,
    RefCrime,
    RefLightBlind,
    RefPolice,
    RefPolicePopulation,
    RefSafePath,
)
from scripts.seeders.common import (
    float_or_none,
    int_or_none,
    load_csv,
    make_point,
    seed_table,
    str_or_none,
)


async def seed_security(session, data_dir: Path, *, replace: bool = False) -> dict[str, int]:
    base = data_dir / "치안리스크"
    results: dict[str, int] = {}

    df = load_csv(base / "master_security_cctv.csv")
    results["ref_cctv"] = await seed_table(session, RefCctv, [
        {
            "agency": str_or_none(row["관리기관명"]),
            "address": str_or_none(row["소재지도로명주소"]),
            "lat": float(row["lat"]),
            "lon": float(row["lon"]),
            "geom": make_point(row["lon"], row["lat"]),
            "raw_score": float_or_none(row["raw_score_cctv"]),
        }
        for _, row in df.iterrows()
    ], replace=replace)

    df = load_csv(base / "master_security_light_blind.csv")
    results["ref_light_blind"] = await seed_table(session, RefLightBlind, [
        {
            "mgmt_no": str_or_none(row["관리번호"]),
            "lat": float(row["위도"]),
            "lon": float(row["경도"]),
            "geom": make_point(row["경도"], row["위도"]),
            "dist_to_nearest": float_or_none(row["dist_to_nearest"]),
            "is_blind": bool(row["is_blind"]),
            "raw_score": float_or_none(row["raw_score_light_blind"]),
        }
        for _, row in df.iterrows()
    ], replace=replace)

    df = load_csv(base / "master_security_police_fixed.csv")
    results["ref_police"] = await seed_table(session, RefPolice, [
        _police_record(row)
        for _, row in df.iterrows()
    ], replace=replace)

    df = load_csv(base / "master_security_crime.csv")
    results["ref_crime"] = await seed_table(session, RefCrime, [
        {"gu_name": str_or_none(row["자치구명"]), "raw_score": float_or_none(row["raw_score_crime"])}
        for _, row in df.iterrows()
    ], replace=replace)

    df = load_csv(base / "master_security_police_pop.csv")
    results["ref_police_pop"] = await seed_table(session, RefPolicePopulation, [
        {
            "gu_name": str_or_none(row["자치구명"]),
            "dong_code": str_or_none(row["adstrd_code_se"]),
            "population": float_or_none(row["tot_lvpop_co"]),
            "police_count": int_or_none(row["2025년"]),
            "raw_score": float_or_none(row["raw_score_police_per_pop"]),
        }
        for _, row in df.iterrows()
    ], replace=replace)

    df = load_csv(base / "master_security_cctv_growth.csv")
    results["ref_cctv_growth"] = await seed_table(session, RefCctvGrowth, [
        {
            "gu_name": str_or_none(row["구분"]),
            "count_2015": int_or_none(row["2015년"]),
            "count_2025": int_or_none(row["2025년"]),
            "growth_rate": float_or_none(row["CCTV_10년_증가율"]),
            "raw_score": float_or_none(row["raw_score_cctv_growth"]),
        }
        for _, row in df.iterrows()
    ], replace=replace)

    df = load_csv(base / "master_security_safepath_fixed.csv")
    results["ref_safepath"] = await seed_table(session, RefSafePath, [
        {
            "region_code": str_or_none(row["행정구역명"]),
            "length_m": float_or_none(row["길이_num"]),
            "raw_score": float_or_none(row["raw_score_safe_path"]),
        }
        for _, row in df.iterrows()
    ], replace=replace)

    return results


def _police_record(row) -> dict:
    record = {
        "station": str_or_none(row["경찰서"]),
        "office_name": str_or_none(row["관서명"]),
        "category": str_or_none(row["구분"]),
        "address": str_or_none(row.get("clean_address") or row.get("주소")),
        "lat": _float_or_none(row.get("lat")),
        "lon": _float_or_none(row.get("lon")),
        "raw_score": float_or_none(row["raw_score_police"]),
    }
    geom = _make_point_or_none(row.get("lon"), row.get("lat"))
    if geom is not None:
        record["geom"] = geom
    return record


def _float_or_none(value) -> float | None:
    if value in (None, ""):
        return None
    return float_or_none(value)


def _make_point_or_none(lon, lat):
    if lon in (None, "") or lat in (None, ""):
        return None
    return make_point(lon, lat)
