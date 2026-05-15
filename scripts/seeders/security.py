from pathlib import Path
from typing import Any

import pandas as pd

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


CRIME_TYPES = [
    ("murder", "살인"),
    ("robbery", "강도"),
    ("sexual_crime", "강간"),
    ("theft", "절도"),
    ("violence", "폭력"),
]


async def seed_security(session, data_dir: Path, *, replace: bool = False) -> dict[str, int]:
    base = data_dir / "치안리스크"
    results: dict[str, int] = {}

    df = load_csv(base / "master_security_cctv_cleaned.csv")
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

    df = load_csv(base / "master_security_light_safe_bonus.csv")
    results["ref_light_blind"] = await seed_table(session, RefLightBlind, [
        {
            "mgmt_no": str_or_none(row["관리번호"]),
            "lat": float(row["위도"]),
            "lon": float(row["경도"]),
            "geom": make_point(row["경도"], row["위도"]),
            "dist_to_nearest": float_or_none(row["dist_to_nearest_m"]),
            # Keep the legacy DB column but store the final-data meaning: safe spot.
            "is_blind": bool_or_none(row["is_safe_spot"]) or False,
            "raw_score": float_or_none(row["safe_bonus_score"]),
        }
        for _, row in df.iterrows()
    ], replace=replace)

    df = load_csv(base / "master_security_police_fixed_updated.csv")
    results["ref_police"] = await seed_table(session, RefPolice, [
        _police_record(row)
        for _, row in df.iterrows()
    ], replace=replace)

    results["ref_crime"] = await seed_table(
        session,
        RefCrime,
        _crime_records(base / "master_security_crime.csv"),
        replace=replace,
    )

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

    results["ref_cctv_growth"] = await seed_table(
        session,
        RefCctvGrowth,
        _cctv_growth_records(base / "master_security_cctv_growth.csv"),
        replace=replace,
    )

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


def _crime_records(path: Path) -> list[dict]:
    raw = _load_raw_csv(path)
    if _has_column(raw, "raw_score_crime"):
        df = load_csv(path)
        return [
            {
                "gu_name": str_or_none(row.get("자치구명") or row.get("자치구별")),
                "raw_score": float_or_none(row["raw_score_crime"]),
                "detail_json": None,
            }
            for _, row in df.iterrows()
        ]

    years = [_year_value(value) for value in raw.iloc[0, 1:].tolist()]
    crime_kinds = [str(value).strip() for value in raw.iloc[1, 1:].tolist()]
    metrics = [str(value).strip() for value in raw.iloc[2, 1:].tolist()]
    rows = raw.iloc[3:].reset_index(drop=True)

    parsed: list[dict] = []
    for _, row in rows.iterrows():
        gu_name = str_or_none(row.iloc[0])
        if not gu_name:
            continue
        year_data = _crime_year_data(row, years, crime_kinds, metrics)
        total_occurrence = _average(
            values["전체"]["발생"] for values in year_data.values()
        )
        parsed.append(
            {
                "gu_name": gu_name,
                "raw_score": total_occurrence,
                "year_data": year_data,
            }
        )

    seoul_avg = _average(item["raw_score"] for item in parsed)
    seoul_clearance_rate = _clearance_rate_for_items(parsed)
    sorted_by_safe = sorted(parsed, key=lambda item: item["raw_score"])

    records: list[dict] = []
    for item in parsed:
        rank = next(index for index, ranked in enumerate(sorted_by_safe, start=1) if ranked["gu_name"] == item["gu_name"])
        records.append(
            {
                "gu_name": item["gu_name"],
                "raw_score": item["raw_score"],
                "detail_json": {
                    "years": sorted(item["year_data"].keys()),
                    "summary": {
                        "total_occurrence": round(item["raw_score"]),
                        "occurrence_diff_from_seoul_avg": _percent_diff(item["raw_score"], seoul_avg),
                        "clearance_rate": _clearance_rate_for_year_data(item["year_data"], "전체"),
                        "seoul_clearance_rate": seoul_clearance_rate,
                        "rank": rank,
                        "rank_total": len(parsed),
                        "safe_percentile": round(rank / len(parsed) * 100, 1),
                    },
                    "items": _crime_chart_items(item["year_data"]),
                },
            }
        )
    return records


def _crime_year_data(row, years: list[int], crime_kinds: list[str], metrics: list[str]) -> dict[int, dict]:
    result: dict[int, dict] = {}
    for offset, raw_value in enumerate(row.iloc[1:].tolist()):
        year = years[offset]
        kind = crime_kinds[offset]
        metric = metrics[offset]
        result.setdefault(year, {}).setdefault(kind, {})[metric] = _float_value(raw_value)
    return result


def _crime_chart_items(year_data: dict[int, dict]) -> list[dict]:
    averages: list[dict] = []
    for type_key, label in CRIME_TYPES:
        occurrence = _average(values[label]["발생"] for values in year_data.values())
        clearance_rate = _clearance_rate_for_year_data(year_data, label)
        averages.append(
            {
                "type": type_key,
                "label": label,
                "occurrence": round(occurrence),
                "clearance_rate": clearance_rate,
            }
        )

    max_occurrence = max((item["occurrence"] for item in averages), default=0)
    for item in averages:
        item["bar_value"] = (
            max(1, round(item["occurrence"] / max_occurrence * 100))
            if max_occurrence and item["occurrence"] > 0
            else 0
        )
        item["status"] = _status_from_bar(item["bar_value"])
        item["display_occurrence"] = f"{item['occurrence']:,}건"
        item["display_clearance_rate"] = (
            f"검거 {item['clearance_rate']:.0f}%"
            if item["clearance_rate"] is not None
            else "검거 —"
        )
    return averages


def _clearance_rate_for_year_data(year_data: dict[int, dict], kind: str) -> float | None:
    occurrence = sum(values[kind]["발생"] for values in year_data.values())
    arrests = sum(values[kind]["검거"] for values in year_data.values())
    if occurrence <= 0:
        return None
    return _clamp_percent(arrests / occurrence * 100)


def _clearance_rate_for_items(items: list[dict]) -> float | None:
    occurrence = 0.0
    arrests = 0.0
    for item in items:
        for values in item["year_data"].values():
            occurrence += values["전체"]["발생"]
            arrests += values["전체"]["검거"]
    if occurrence <= 0:
        return None
    return _clamp_percent(arrests / occurrence * 100)


def _cctv_growth_records(path: Path) -> list[dict]:
    raw = _load_raw_csv(path)
    if _has_column(raw, "raw_score_cctv_growth"):
        df = load_csv(path)
        return [
            {
                "gu_name": str_or_none(row["구분"]),
                "count_2015": int_or_none(row["2015년"]),
                "count_2025": int_or_none(row["2025년"]),
                "growth_rate": float_or_none(row["CCTV_10년_증가율"]),
                "raw_score": float_or_none(row["raw_score_cctv_growth"]),
                "detail_json": None,
            }
            for _, row in df.iterrows()
        ]

    years = [_year_value(value) for value in raw.iloc[0, 1::2].tolist()]
    rows = raw.iloc[2:].reset_index(drop=True)
    records: list[dict] = []
    for _, row in rows.iterrows():
        gu_name = str_or_none(row.iloc[0])
        counts = [_int_value(value) for value in row.iloc[1::2].tolist()]
        first_count = counts[0] if counts else None
        last_count = counts[-1] if counts else None
        growth_rate = _growth_rate(first_count, last_count)
        records.append(
            {
                "gu_name": gu_name,
                # Legacy column name; final data starts from 2016.
                "count_2015": first_count,
                "count_2025": last_count,
                "growth_rate": growth_rate,
                "raw_score": growth_rate,
                "detail_json": {
                    "years": years,
                    "counts": counts,
                    "growth_rate": growth_rate,
                    "growth_label": _growth_label(years, growth_rate),
                },
            }
        )
    return records


def _police_record(row) -> dict:
    record = {
        "station": str_or_none(row["경찰서"]),
        "office_name": str_or_none(row["관서명"]),
        "category": str_or_none(row["구분"]),
        "address": str_or_none(row.get("clean_address") or row.get("주소")),
        "lat": _float_or_none(row.get("lat")),
        "lon": _float_or_none(row.get("lon")),
        "geom": _make_point_or_none(row.get("lon"), row.get("lat")),
        "raw_score": float_or_none(row["raw_score_police"]),
    }
    return record


def bool_or_none(value: Any) -> bool | None:
    if pd.isna(value):
        return None
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"true", "1", "yes", "y"}


def _load_raw_csv(path: Path) -> pd.DataFrame:
    for encoding in ("utf-8-sig", "euc-kr"):
        try:
            return pd.read_csv(path, encoding=encoding, header=None)
        except UnicodeDecodeError:
            continue
    return pd.read_csv(path, header=None)


def _has_column(raw: pd.DataFrame, column_name: str) -> bool:
    return column_name in {str(value) for value in raw.iloc[0].tolist()}


def _year_value(value) -> int:
    return int(str(value).split(".")[0])


def _average(values) -> float:
    numeric = [float(value) for value in values if value is not None]
    return sum(numeric) / len(numeric) if numeric else 0.0


def _float_value(value) -> float:
    if pd.isna(value):
        return 0.0
    return float(value)


def _int_value(value) -> int | None:
    if pd.isna(value):
        return None
    return int(float(value))


def _growth_rate(first: int | None, last: int | None) -> float | None:
    if not first or last is None:
        return None
    return round((last - first) / first * 100, 1)


def _growth_label(years: list[int], growth_rate: float | None) -> str | None:
    if not years or growth_rate is None:
        return None
    return f"{str(years[0])[-2:]}→{str(years[-1])[-2:]}년 +{growth_rate:g}%"


def _percent_diff(value: float, baseline: float) -> float | None:
    if baseline <= 0:
        return None
    return round((value - baseline) / baseline * 100, 1)


def _clamp_percent(value: float) -> float:
    return max(0.0, min(100.0, round(value, 1)))


def _status_from_bar(value: int) -> str:
    if value >= 70:
        return "위험"
    if value >= 35:
        return "주의"
    return "안심"


def _float_or_none(value) -> float | None:
    if value in (None, ""):
        return None
    return float_or_none(value)


def _make_point_or_none(lon, lat):
    if lon in (None, "") or lat in (None, ""):
        return None
    return make_point(lon, lat)
