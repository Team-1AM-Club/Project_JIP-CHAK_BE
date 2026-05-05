# 불완전: 비교 계산 로직은 구현됐지만 실제 report/bookmark 데이터 기반 통합 테스트와 추천 문구 고도화가 필요함.
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import REPORT_CATEGORIES, grade_from_score
from app.core.exceptions import AppException
from app.models.user import User
from app.services import bookmark_service, report_service
from app.services.analysis.scorer import calculate_total_score
from app.services.user_service import weights_from_user


async def compare_reports(db: AsyncSession, user: User, report_ids: list[UUID]) -> dict:
    if len(report_ids) < 2 or len(report_ids) > 4:
        raise AppException(400, "INVALID_COMPARISON_COUNT", "비교 대상 개수가 올바르지 않습니다.")

    reports = [await report_service.get_owned_report(db, user, report_id) for report_id in report_ids]
    weights = weights_from_user(user)
    report_scores = {report.report_id: report_service.category_scores(report) for report in reports}
    totals = {
        report.report_id: calculate_total_score(report_scores[report.report_id], weights)
        for report in reports
    }

    return {
        "reports": [
            {
                "report_id": report.report_id,
                "address": report.address,
                "short_address": _short_address(report.address),
                "region_name": _region_name(report.address),
                "rank_label": chr(ord("A") + index),
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
        raise AppException(400, "INVALID_INPUT_VALUE", "유효하지 않은 입력 값입니다.") from exc


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
                "label": meta["title"].replace(" 리스크", "").replace(" 접근성", ""),
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
    best_category = max(scores, key=scores.get)
    return [REPORT_CATEGORIES[best_category]["title"]]


def _short_address(address: str) -> str:
    parts = address.split()
    return " ".join(parts[-2:]) if len(parts) >= 2 else address


def _region_name(address: str) -> str | None:
    return next((part for part in address.split() if part.endswith("구")), None)
