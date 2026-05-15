from app.core.meta_stats import get_stat
from app.models.report import Report
from app.services.analysis.detail import data_source, indicator, indicator_chart
from app.services.analysis.scorer import normalize, weighted_sum


def calculate_security_score(report: Report) -> int:
    if report.security_score is not None and not (report.safety_map or {}).get("crime_detail"):
        return report.security_score
    indicators = _indicator_scores(report)
    return weighted_sum([(item["score"], item["weight"]) for item in indicators])


def get_security_detail(report: Report) -> dict:
    score = calculate_security_score(report)
    indicators = _indicator_scores(report)
    return {
        "score": score,
        "base_score": score,
        "summary": _summary(score, report),
        "indicators": indicators,
        "visualization": {
            "type": "security_detail",
            "center": {"lat": report.lat, "lng": report.lng},
            "chart": indicator_chart(indicators),
            "security_infra_chart": _security_infra_chart(report),
            "crime_chart": _crime_chart(report),
            "layers": [
                {"type": "CCTV", "name": "주변 CCTV", "source": "master_security_cctv_cleaned.csv"},
                {"type": "CCTV_GROWTH", "name": "CCTV 증가율", "source": "master_security_cctv_growth.csv"},
                {"type": "CRIME", "name": "5대 범죄", "source": "master_security_crime.csv"},
                {"type": "LIGHT_SAFE", "name": "가로등·안전스팟", "source": "master_security_light_safe_bonus.csv"},
                {"type": "POLICE", "name": "파출소·지구대", "source": "master_security_police_fixed_updated.csv"},
                {"type": "POLICE_POP", "name": "경찰 인구비", "source": "master_security_police_pop.csv"},
                {"type": "SAFE_PATH", "name": "안심귀갓길", "source": "master_security_safepath_fixed.csv"},
            ],
            "data": report.safety_map,
        },
        "data_source": data_source("5대 범죄, CCTV, 조도 안전도, 안심귀갓길, 경찰 시설 전처리 데이터 기반"),
    }


def _indicator_scores(report: Report) -> list[dict]:
    crime_score = _score("security_crime", report.crime_count, inverse=True)
    cctv_score = _score("security_cctv", report.cctv_count)
    cctv_growth_score = _score("security_cctv_growth", report.cctv_growth)
    light_score = _score("security_light_blind", report.light_blind_ratio)
    safepath_score = _score("security_safepath", report.safepath_score)
    police_score = _score("security_police", report.police_count)

    return [
        _indicator_with_status(
            key="crime_count",
            name="범죄 발생",
            raw_value=round(report.crime_count),
            unit="건",
            score=crime_score,
            weight=0.25,
        ),
        _indicator_with_status(
            key="cctv_density",
            name="CCTV 수",
            raw_value=round(report.cctv_count),
            unit="개",
            score=cctv_score,
            weight=0.15,
        ),
        _indicator_with_status(
            key="cctv_growth",
            name="CCTV 증가율",
            raw_value=report.cctv_growth,
            unit="%",
            score=cctv_growth_score,
            weight=0.10,
        ),
        _indicator_with_status(
            key="light_safety",
            name="조도 안전도",
            raw_value=report.light_blind_ratio,
            unit="점",
            score=light_score,
            weight=0.15,
        ),
        _indicator_with_status(
            key="safepath_score",
            name="안심귀갓길",
            raw_value=report.safepath_score,
            unit="점",
            score=safepath_score,
            weight=0.15,
            display_value_override=_score_display(safepath_score),
        ),
        _indicator_with_status(
            key="police_access",
            name="경찰 접근성",
            raw_value=report.police_count,
            unit="점",
            score=police_score,
            weight=0.20,
            display_value_override=_score_display(police_score),
        ),
    ]


def _security_infra_chart(report: Report) -> dict:
    safety_map = report.safety_map or {}
    cctv_detail = safety_map.get("cctv_growth_detail") or {}
    cctv_map = safety_map.get("cctv") or {}
    street_light = safety_map.get("street_light") or {}
    nearest_police = safety_map.get("nearest_police") or {}

    nearby_cctv = int(round(cctv_map.get("nearby_count") or report.cctv_count or 0))
    light_count = int(street_light.get("nearby_count") or 0)
    safe_spot_count = int(street_light.get("safe_spot_count") or 0)
    radius_m = int(street_light.get("radius_m") or 500)
    density = round(light_count / radius_m, 2) if radius_m else None
    avg_safe_bonus_score = street_light.get("avg_safe_bonus_score")

    distance_m = nearest_police.get("distance_m")
    rounded_distance = round(distance_m) if distance_m is not None else None

    return {
        "cctv": {
            "title": "CCTV",
            "status": _infra_status(_score("security_cctv", nearby_cctv)),
            "nearby_count": nearby_cctv,
            "radius_m": int(cctv_map.get("radius_m") or 500),
            "years": cctv_detail.get("years", []),
            "counts": cctv_detail.get("counts", []),
            "growth_rate": cctv_detail.get("growth_rate"),
            "growth_label": cctv_detail.get("growth_label"),
        },
        "street_light": {
            "title": "조도 안전도",
            "status": _infra_status(_score("security_light_blind", report.light_blind_ratio)),
            "nearby_count": light_count,
            "radius_m": radius_m,
            "density": density,
            "density_label": f"밀도 {density}개/m" if density is not None else "밀도 확인 필요",
            "safe_spot_count": safe_spot_count,
            "safe_spot_label": f"안전스팟 {safe_spot_count}곳",
            "avg_safe_bonus_score": avg_safe_bonus_score,
        },
        "police": {
            "title": "가장 가까운 파출소",
            "name": nearest_police.get("name") or "가까운 파출소",
            "distance_m": rounded_distance,
            "distance_label": f"{rounded_distance}m" if rounded_distance is not None else "거리 데이터 없음",
            "travel_label": _walk_time_label(rounded_distance),
        },
    }


def _crime_chart(report: Report) -> dict | None:
    safety_map = report.safety_map or {}
    detail = safety_map.get("crime_detail")
    if not detail:
        return None
    return {
        "title": "5대 범죄 발생",
        "subtitle": "최근 5년 평균",
        "scope": "자치구 기준",
        "gu_name": safety_map.get("gu_name"),
        "display_region_name": safety_map.get("display_region_name"),
        "years": detail.get("years", []),
        "summary": detail.get("summary", {}),
        "items": detail.get("items", []),
    }


def _summary(score: int, report: Report) -> str:
    safety_map = report.safety_map or {}
    crime_detail = safety_map.get("crime_detail") or {}
    summary = crime_detail.get("summary") or {}
    diff = summary.get("occurrence_diff_from_seoul_avg")
    if score >= 80:
        return "범죄 발생과 안전 인프라 지표가 전반적으로 양호해 야간 이동 안정성이 높은 편입니다."
    if diff is not None and diff < 0:
        return "범죄 발생은 평균보다 낮지만, 조도 안전도와 안심귀갓길 접근성을 함께 확인하는 것이 좋습니다."
    if score >= 40:
        return "치안 지표 일부에 주의가 필요해 야간 이동 시 밝은 경로와 가까운 파출소 위치를 확인하는 것이 좋습니다."
    return "범죄 발생과 안전 인프라 지표가 낮아 야간 이동 전 주변 환경 확인이 필요합니다."


def _indicator_with_status(**kwargs) -> dict:
    item = indicator(**kwargs)
    item["status"] = _score_status(item["score"])
    return item


def _score_status(score: int | None) -> str:
    if score is None:
        return "분석중"
    if score >= 80:
        return "안심"
    if score >= 60:
        return "양호"
    if score >= 40:
        return "주의"
    return "위험"


def _infra_status(score: int | None) -> str:
    if score is None:
        return "확인 필요"
    if score >= 80:
        return "충분"
    if score >= 60:
        return "보통"
    return "부족"


def _walk_time_label(distance_m: int | None) -> str:
    if distance_m is None:
        return "확인 필요"
    minutes = max(1, round(distance_m / 67))
    return f"도보 {minutes}분"


def _score(
    key: str,
    value: float | int | None,
    *,
    inverse: bool = False,
    fallback: int | None = None,
) -> int | None:
    stat = get_stat(key)
    if not stat or value is None:
        return fallback
    return normalize(value, stat["p05"], stat["p95"], inverse=inverse)


def _score_display(score: int | None) -> str | None:
    return f"{score}점" if score is not None else None
