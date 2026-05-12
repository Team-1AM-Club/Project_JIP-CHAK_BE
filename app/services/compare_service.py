# 비교 API: 주소 2개를 입력받아 각각 리포트를 생성하고 1:1 비교 결과를 반환한다.
import logging
from uuid import UUID, uuid4

from fastapi import BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import REPORT_CATEGORIES, grade_from_score
from app.core.exceptions import AppException
from app.core.task_status import get_task_status, set_task_status
from app.db.session import AsyncSessionLocal
from app.external.ai_report import generate_comparison_recommendation
from app.models.report import Report
from app.models.user import User
from app.services import bookmark_service, report_service
from app.services.analysis.scorer import calculate_total_score
from app.services.user_service import weights_from_user

logger = logging.getLogger(__name__)

REQUIRED_COMPARE_COUNT = 2


async def start_comparison(
    db: AsyncSession,
    user: User,
    addresses: list[dict],
    background_tasks: BackgroundTasks,
) -> dict:
    """비교 요청 진입점. 캐시 전부 히트 시 즉시 결과 반환, 아니면 Background Task 발급."""
    _validate_address_count(addresses)
    for addr in addresses:
        _validate_seoul(addr)

    cached_reports = await _try_all_cached(db, user, addresses)
    if cached_reports is not None:
        result = await _build_comparison(db, user, cached_reports)
        return {"status": "READY", **result}

    task_id = uuid4()
    await set_task_status(
        task_id,
        {
            "status": "PROCESSING",
            "progress": 0,
            "current_step": "비교 분석 준비 중",
            "completed_addresses": 0,
        },
    )
    background_tasks.add_task(run_comparison_analysis, task_id, user.user_id, addresses)
    return {"status": "PROCESSING", "task_id": task_id}


async def run_comparison_analysis(task_id: UUID, user_id: UUID, addresses: list[dict]) -> None:
    """Background Task: 주소 2개를 순차 분석 후 비교 결과를 Redis에 저장."""
    async with AsyncSessionLocal() as db:
        try:
            user = await db.get(User, user_id)
            if user is None:
                raise AppException(404, "USER_NOT_FOUND", "사용자를 찾을 수 없습니다.")

            reports = []
            for i, addr in enumerate(addresses):
                report = await report_service.analyze_single_address(db, user, addr)
                reports.append(report)
                await set_task_status(
                    task_id,
                    {
                        "status": "PROCESSING",
                        "progress": int((i + 1) / len(addresses) * 80),
                        "current_step": f"주소 {i + 1}번 분석 완료",
                        "completed_addresses": i + 1,
                    },
                )

            await db.commit()
            result = await _build_comparison(db, user, reports)
            await set_task_status(
                task_id,
                {
                    "status": "COMPLETED",
                    "progress": 100,
                    "data": result,
                },
            )
        except Exception as exc:
            await db.rollback()
            logger.exception("비교 분석 작업 실패: task_id=%s", task_id)
            await set_task_status(
                task_id,
                {
                    "status": "FAILED",
                    "progress": 100,
                    "error": {
                        "code": "COMPARISON_FAILED",
                        "message": "비교 처리 중 오류가 발생했습니다.",
                        "details": str(exc),
                    },
                },
            )


async def get_comparison_status(task_id: UUID) -> dict:
    status = await get_task_status(task_id)
    if status is None:
        raise AppException(404, "TASK_NOT_FOUND", "비교 분석 작업을 찾을 수 없습니다.")
    return status


async def _try_all_cached(
    db: AsyncSession, user: User, addresses: list[dict]
) -> list[Report] | None:
    """모든 주소가 본인 캐시 히트하면 Report 리스트 반환, 하나라도 미스면 None."""
    reports = []
    for addr in addresses:
        region_code = addr.get("dong_code") or "UNKNOWN"
        cached = await report_service.find_cached_report(db, user.user_id, region_code)
        if cached is None:
            return None
        reports.append(cached)
    return reports


async def _build_comparison(db: AsyncSession, user: User, reports: list[Report]) -> dict:
    """리포트 2개로 비교 결과 dict 생성."""
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
                "rank_label": _rank_label(index),
                "total_score": totals[report.report_id],
                "grade": grade_from_score(totals[report.report_id]),
                "strength_tags": _strength_tags(report_scores[report.report_id]),
                "saved": await bookmark_service.is_bookmarked(db, user, report.report_id),
            }
            for index, report in enumerate(reports)
        ],
        "metric_comparison": _metric_comparison(reports, report_scores),
        "recommendation": await _recommendation(reports, totals, report_scores),
    }


def _metric_comparison(reports: list[Report], report_scores: dict) -> list[dict]:
    first = reports[0]
    metrics = []
    for category, meta in REPORT_CATEGORIES.items():
        scores = [
            {
                "report_id": report.report_id,
                "score": report_scores[report.report_id][category],
                "diff": report_scores[report.report_id][category] - report_scores[first.report_id][category],
            }
            for report in reports
        ]
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


async def _recommendation(
    reports: list[Report], totals: dict, report_scores: dict
) -> dict:
    best_report = max(reports, key=lambda report: totals[report.report_id])
    other_report = next(r for r in reports if r.report_id != best_report.report_id)

    ai_content = await generate_comparison_recommendation(
        address_a=best_report.address,
        address_b=other_report.address,
        scores_a=report_scores[best_report.report_id],
        scores_b=report_scores[other_report.report_id],
        total_a=totals[best_report.report_id],
        total_b=totals[other_report.report_id],
        recommended_address=best_report.address,
    )

    return {
        "title": "사용자 가중치 기준 종합 추천",
        "content": ai_content or f"{best_report.address}가 현재 가중치 기준으로 가장 높은 종합 점수입니다.",
        "recommended_report_id": best_report.report_id,
        "basis": "현재 사용자 가중치 기준",
    }


def _validate_address_count(addresses: list[dict]) -> None:
    if len(addresses) != REQUIRED_COMPARE_COUNT:
        raise AppException(
            400,
            "INVALID_COMPARISON_COUNT",
            f"비교 대상 주소는 정확히 {REQUIRED_COMPARE_COUNT}개여야 합니다.",
        )


def _validate_seoul(addr: dict) -> None:
    dong_code = addr.get("dong_code")
    address = addr.get("address", "")
    road_addr = addr.get("road_addr")
    jibun_addr = addr.get("jibun_addr")
    if dong_code and dong_code.startswith("11"):
        return
    if any(a and ("서울" in a or "Seoul" in a) for a in [address, road_addr, jibun_addr]):
        return
    raise AppException(400, "OUT_OF_SERVICE_AREA", "서울시 내 주소만 비교 가능합니다.")


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
