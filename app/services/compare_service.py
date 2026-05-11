# 완벽: 비교 API는 사용자 소유 리포트 검증 후 2개 이상 다중 리포트의 카테고리/총점을 비교하도록 구현됨.
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import REPORT_CATEGORIES, grade_from_score
from app.core.exceptions import AppException
from app.models.user import User
from app.services import bookmark_service, report_service
from app.services.analysis.scorer import calculate_total_score
from app.services.user_service import weights_from_user

MIN_COMPARE_REPORTS = 2
MAX_COMPARE_REPORTS = 10


async def compare_reports(db: AsyncSession, user: User, report_ids: list[UUID]) -> dict:
    _validate_report_ids(report_ids)

    reports = [await report_service.get_owned_report(db, user, report_id) for report_id in report_ids]
    weights = weights_from_user(user)
    report_scores = {report.report_id: report_service.category_scores(report) for report in reports}
    totals = {
        report.report_id: calculate_total_score(report_scores[report.report_id], weights)
        for report in reports
    }

    return {
        "compare_count": len(reports),
        "reports": [
            {
                "report_id": report.report_id,
                "address": report.address,
                "short_address": _short_address(report.address),
                "region_name": _region_name(report.address),
                "rank_label": _rank_label(index),
                "total_score": totals[report.report_id],
                "grade": grade_from_score(totals[report.report_id]),
                "strength_tags": _strength_tags(report_scores[report.report_id]),
                "saved": await bookmark_service.is_bookmarked(db, user, report.report_id),
            }
            for index, report in enumerate(reports)
        ],
        "metric_comparison": _metric_comparison(reports, report_scores),
        "recommendation": _recommendation(reports, totals),
    }


def parse_report_ids(value: str) -> list[UUID]:
    try:
        return [UUID(item.strip()) for item in value.split(",") if item.strip()]
    except ValueError as exc:
        raise AppException(400, "INVALID_INPUT_VALUE", "유효하지 않은 리포트 ID입니다.") from exc


def _validate_report_ids(report_ids: list[UUID]) -> None:
    if len(report_ids) < MIN_COMPARE_REPORTS or len(report_ids) > MAX_COMPARE_REPORTS:
        raise AppException(
            400,
            "INVALID_COMPARISON_COUNT",
            f"비교 대상은 {MIN_COMPARE_REPORTS}개 이상 {MAX_COMPARE_REPORTS}개 이하로 선택해야 합니다.",
        )
    if len(set(report_ids)) != len(report_ids):
        raise AppException(400, "DUPLICATE_REPORT_ID", "같은 리포트를 중복 비교할 수 없습니다.")


def _metric_comparison(reports, report_scores: dict) -> list[dict]:
    first = reports[0]
    metrics = []
    for category, meta in REPORT_CATEGORIES.items():
        scores = []
        for report in reports:
            score = report_scores[report.report_id][category]
            scores.append(
                {
                    "report_id": report.report_id,
                    "score": score,
                    "diff": score - report_scores[first.report_id][category],
                }
            )
        best = max(scores, key=lambda item: item["score"])
        metrics.append(
            {
                "type": category,
                "label": _metric_label(meta["title"]),
                "icon": meta["icon"],
                "scores": scores,
                "best_report_id": best["report_id"],
            }
        )
    return metrics


def _recommendation(reports, totals: dict) -> dict:
    best_report = max(reports, key=lambda report: totals[report.report_id])
    return {
        "title": "사용자 가중치 기준 종합 추천",
        "content": f"{best_report.address}가 현재 가중치 기준으로 가장 높은 종합 점수입니다.",
        "recommended_report_id": best_report.report_id,
        "basis": "현재 사용자 가중치 기준",
    }


def _strength_tags(scores: dict[str, int]) -> list[str]:
    sorted_categories = sorted(scores, key=scores.get, reverse=True)
    return [REPORT_CATEGORIES[category]["title"] for category in sorted_categories[:2]]


def _metric_label(title: str) -> str:
    return title.replace(" 리스크", "").replace(" 접근성", "").replace("생활 ", "")


def _rank_label(index: int) -> str:
    return chr(ord("A") + index) if index < 26 else str(index + 1)


def _short_address(address: str) -> str:
    parts = address.split()
    return " ".join(parts[-2:]) if len(parts) >= 2 else address


def _region_name(address: str) -> str | None:
    return next((part for part in address.split() if part.endswith("구")), None)
