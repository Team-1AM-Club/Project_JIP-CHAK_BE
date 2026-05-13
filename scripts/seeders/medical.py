from pathlib import Path

from app.models.reference.medical import (
    RefHealthDong,
    RefHealthWorkforce,
    RefNightClinic,
    RefPharmacy,
)
from scripts.seeders.common import float_or_none, int_or_none, load_csv, make_point, seed_table, str_or_none


async def seed_medical(session, data_dir: Path, *, replace: bool = False) -> dict[str, int]:
    base = data_dir / "의료접근성"
    results: dict[str, int] = {}

    df = load_csv(base / "master_map_night_clinics_point_fixed.csv")
    results["ref_night_clinic"] = await seed_table(session, RefNightClinic, [
        {
            "name": str_or_none(row.get("명") or row.get("기관명")),
            "gu_name": str_or_none(row.get("자치구명") or row.get("주소")),
            "dong_name": str_or_none(row.get("동") or row.get("행정동명")),
            "lat": float(row["위도"]),
            "lon": float(row["경도"]),
            "geom": make_point(row["경도"], row["위도"]),
            "raw_score": float_or_none(row["raw_score_clinic_point"]),
        }
        for _, row in df.iterrows()
    ], replace=replace)

    df = load_csv(base / "master_map_pharmacy_point_converted.csv")
    results["ref_pharmacy"] = await seed_table(session, RefPharmacy, [
        {
            "name": str_or_none(row.get("명") or row.get("사업장명")),
            "gu_name": str_or_none(row["자치구명"]),
            "dong_name": str_or_none(row.get("동") or row.get("행정동명")),
            "lat": float(row["위도"]),
            "lon": float(row["경도"]),
            "geom": make_point(row["경도"], row["위도"]),
            "raw_score": float_or_none(row["raw_score_pharmacy_point"]),
        }
        for _, row in df.iterrows()
    ], replace=replace)

    df = load_csv(base / "master_health_facilities_dong.csv")
    results["ref_health_dong"] = await seed_table(session, RefHealthDong, [
        {
            "gu_name": str_or_none(row["자치구명"]),
            "dong_name": str_or_none(row["동"]),
            "night_clinic_count": float_or_none(row["야간의료시설수"]),
            "raw_score_clinic": float_or_none(row["raw_score_night_clinic"]),
            "pharmacy_count": float_or_none(row["약국수"]),
            "raw_score_pharmacy": float_or_none(row["raw_score_pharmacy"]),
        }
        for _, row in df.iterrows()
    ], replace=replace)

    df = load_csv(base / "master_health_workforce_gu.csv")
    results["ref_health_workforce"] = await seed_table(session, RefHealthWorkforce, [
        {
            "gu_name": str_or_none(row["자치구명"]),
            "nurse_count": int_or_none(row["간호사수"]),
            "specialist_count": int_or_none(row["전문의"]),
            "raw_score": float_or_none(row["raw_score_medical_staff"]),
        }
        for _, row in df.iterrows()
    ], replace=replace)

    return results
