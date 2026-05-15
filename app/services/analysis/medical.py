from app.core.meta_stats import get_stat
from app.models.report import Report
from app.services.analysis.detail import data_source, indicator, indicator_chart
from app.services.analysis.scorer import clamp_score, normalize, weighted_sum


def calculate_medical_score(report: Report) -> int:
    if report.medical_score is not None:
        return report.medical_score
    indicators = _indicator_scores(report)
    return weighted_sum([(item["score"], item["weight"]) for item in indicators])


def get_medical_detail(report: Report) -> dict:
    score = calculate_medical_score(report)
    indicators = _indicator_scores(report)
    return {
        "score": score,
        "base_score": score,
        "summary": _summary(score, report),
        "indicators": indicators,
        "visualization": {
            "type": "medical_detail",
            "center": {"lat": report.lat, "lng": report.lng},
            "chart": indicator_chart(indicators),
            "nearest_medical_chart": _nearest_medical_chart(report),
            "night_density_chart": _night_density_chart(report),
            "hospital_access_chart": _hospital_access_chart(report),
            "medical_workforce_chart": _medical_workforce_chart(report),
            "layers": [
                {"type": "NIGHT_CLINIC", "name": "야간운영 의료시설", "source": "master_map_night_clinics_point_fixed.csv"},
                {"type": "PHARMACY", "name": "약국", "source": "master_security_pharmacy_individual_latlon.csv"},
                {"type": "HEALTH_WORKFORCE", "name": "의료 인력", "source": "master_health_workforce_gu.csv"},
            ],
            "data": report.medic_map,
        },
        "data_source": data_source("야간운영 의료시설, 약국, 병원 접근성, 의료 인력 전처리 데이터 기반"),
    }


def _indicator_scores(report: Report) -> list[dict]:
    return [
        indicator(
            key="night_medical_density",
            name="야간운영 병의원 수",
            raw_value=report.night_clinic,
            unit="개",
            score=_score("health_night_clinic", report.night_clinic),
            weight=0.35,
        ),
        indicator(
            key="pharmacy_density",
            name="주변 약국 수",
            raw_value=report.pharmacy_count,
            unit="개",
            score=_score("health_pharmacy", report.pharmacy_count),
            weight=0.35,
        ),
        indicator(
            key="public_medical_staff",
            name="구별 의료 인력 수",
            raw_value=report.medical_staff,
            unit="명",
            score=_score("health_workforce_gu", report.medical_staff),
            weight=0.30,
        ),
    ]


def _nearest_medical_chart(report: Report) -> dict:
    nearest = (report.medic_map or {}).get("nearest_medical") or {}
    items = [
        ("general_hospital", "종합병원"),
        ("hospital", "병원"),
        ("clinic", "의원"),
        ("pharmacy", "약국"),
    ]
    return {
        "title": "가까운 의료시설",
        "items": [
            _nearest_item(type_key, label, nearest.get(type_key))
            for type_key, label in items
        ],
    }


def _night_density_chart(report: Report) -> dict:
    data = (report.medic_map or {}).get("night_density") or {}
    time_slots = [
        {
            **slot,
            "status": _count_status(slot.get("count")),
        }
        for slot in data.get("time_slots", [])
    ]
    late_slots = [slot for slot in time_slots if slot.get("hour") in {"00", "02", "04"}]
    late_average = (
        round(sum(slot.get("count", 0) for slot in late_slots) / len(late_slots), 1)
        if late_slots
        else 0.0
    )
    density = data.get("density")
    gu_average = data.get("gu_average")
    return {
        "title": "야간운영 의료시설 밀도",
        "radius_m": data.get("radius_m", 1000),
        "density": density,
        "density_label": f"{density}시설/km²" if density is not None else "밀도 데이터 없음",
        "gu_average": gu_average,
        "gu_average_label": f"자치구 평균 {gu_average}" if gu_average is not None else None,
        "time_slots": time_slots,
        "late_night_summary": {
            "label": "심야(00~04시)",
            "average_count": late_average,
            "description": "약국과 야간 운영 의료시설 기준",
        },
    }


def _hospital_access_chart(report: Report) -> dict:
    data = (report.medic_map or {}).get("hospital_access") or {}
    nearest = data.get("nearest_hospital")
    count = int(data.get("hospital_count") or 0)
    score = _hospital_access_score(count, nearest)
    return {
        "title": "병원 접근성",
        "radius_m": data.get("radius_m", 1000),
        "hospital_count": count,
        "display_count": f"{count}개",
        "access_score": score,
        "status": _score_status(score),
        "nearest_hospital": None if nearest is None else {
            "name": nearest.get("name"),
            "distance_m": _round_distance(nearest.get("distance_m")),
            "distance_label": _distance_label(nearest.get("distance_m")),
        },
    }


def _medical_workforce_chart(report: Report) -> dict:
    medic_map = report.medic_map or {}
    workforce = medic_map.get("workforce") or {}
    averages = medic_map.get("workforce_average") or {}
    items = [
        _workforce_item("nurse", "간호사", workforce.get("nurse_count"), averages.get("nurse")),
        _workforce_item("specialist", "전문의", workforce.get("specialist_count"), averages.get("specialist")),
        _workforce_item("total", "의료 인력 종합", workforce.get("total"), averages.get("total")),
    ]
    return {
        "title": "의료 인력",
        "scope": "자치구 기준",
        "gu_name": medic_map.get("gu_name") or workforce.get("gu_name"),
        "items": items,
    }


def _nearest_item(type_key: str, label: str, item: dict | None) -> dict:
    distance_m = None if item is None else item.get("distance_m")
    return {
        "type": type_key,
        "label": label,
        "name": None if item is None else item.get("name"),
        "distance_m": _round_distance(distance_m),
        "distance_label": _distance_label(distance_m),
        "travel_label": _travel_label(distance_m),
    }


def _workforce_item(key: str, label: str, value, average) -> dict:
    value = float(value or 0.0)
    average = float(average or 0.0)
    diff = _percent_diff(value, average)
    score = _ratio_score(value, average)
    return {
        "key": key,
        "label": label,
        "value": round(value, 1) if value % 1 else int(value),
        "display_value": f"{value:,.0f}명",
        "gu_average": round(average, 1),
        "gu_average_label": f"자치구 평균 {average:,.1f}명",
        "diff_from_average": diff,
        "diff_label": _diff_label(diff),
        "score": score,
        "status": _score_status(score),
    }


def _score(key: str, value: float | int | None, *, inverse: bool = False, fallback: int | None = None) -> int | None:
    stat = get_stat(key)
    if not stat or value is None:
        return fallback
    return normalize(value, stat["p05"], stat["p95"], inverse=inverse)


def _summary(score: int, report: Report) -> str:
    hospital_count = ((report.medic_map or {}).get("hospital_access") or {}).get("hospital_count") or 0
    if score >= 80:
        return "야간 운영 의료시설과 약국 접근성이 좋아 일상 진료 이용이 편리합니다."
    if score >= 60:
        return "의료시설 접근성은 양호하지만, 병원 접근성과 구 단위 의료 인력은 함께 확인하는 것이 좋습니다."
    if hospital_count:
        return "반경 내 병원은 있으나 야간 운영 시설 또는 의료 인력 지표에 보완이 필요합니다."
    return "야간 운영 의료시설과 병원 접근성이 낮아 응급 상황 대비가 필요합니다."


def _hospital_access_score(count: int, nearest: dict | None) -> int:
    count_score = min(60, count * 20)
    distance = None if nearest is None else nearest.get("distance_m")
    if distance is None:
        distance_score = 0
    elif distance <= 500:
        distance_score = 40
    elif distance <= 1000:
        distance_score = 32
    elif distance <= 2000:
        distance_score = 24
    elif distance <= 3000:
        distance_score = 16
    else:
        distance_score = 8
    return clamp_score(count_score + distance_score)


def _ratio_score(value: float, average: float) -> int:
    if average <= 0:
        return 0
    return clamp_score(round(value / average * 60))


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


def _count_status(count: int | None) -> str:
    count = int(count or 0)
    if count >= 10:
        return "안심"
    if count >= 5:
        return "양호"
    if count >= 1:
        return "주의"
    return "위험"


def _round_distance(distance_m) -> int | None:
    return None if distance_m is None else round(float(distance_m))


def _distance_label(distance_m) -> str:
    if distance_m is None:
        return "거리 데이터 없음"
    distance = float(distance_m)
    if distance >= 1000:
        return f"{distance / 1000:.1f}km"
    return f"{round(distance)}m"


def _travel_label(distance_m) -> str:
    if distance_m is None:
        return "확인 필요"
    distance = float(distance_m)
    if distance <= 1000:
        minutes = max(1, round(distance / 67))
        return f"도보 {minutes}분"
    minutes = max(1, round(distance / 250))
    return f"차 {minutes}분"


def _percent_diff(value: float, baseline: float) -> float | None:
    if baseline <= 0:
        return None
    return round((value - baseline) / baseline * 100, 1)


def _diff_label(diff: float | None) -> str:
    if diff is None:
        return "평균 데이터 없음"
    if diff >= 0:
        return f"평균 대비 {diff:.1f}% 높음"
    return f"평균 대비 {abs(diff):.1f}% 낮음"
