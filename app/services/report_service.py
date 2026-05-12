# 불완전: 리포트 조회/점수 응답은 구현됐지만 분석 원천 데이터는 실제 공공데이터 대신 mock interface를 사용함.
import logging
import asyncio
from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

from fastapi import BackgroundTasks
from sqlalchemy import and_, desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import REPORT_CATEGORIES, grade_from_score
from app.core.exceptions import AppException, ForbiddenReportError, ReportNotFoundError
from app.core.task_status import get_task_status, set_task_status
from app.db.session import AsyncSessionLocal
from app.external.public_data import public_data_client
from app.external.ai_report import generate_overall_summary, generate_category_summary
from app.models.bookmark import Bookmark
from app.models.report import Report
from app.models.user import User
from app.services.analysis import congestion, flood, medical, noise, security
from app.services.analysis.scorer import calculate_total_score, summary_for_score
from app.services.user_service import weights_from_user

logger = logging.getLogger(__name__)


async def request_analysis(
    db: AsyncSession,
    user: User,
    payload: dict,
    background_tasks: BackgroundTasks,
) -> dict:
    region_code = payload.get("dong_code")
    if not _is_seoul_location(region_code, payload["address"], payload.get("road_addr"), payload.get("jibun_addr")):
        raise AppException(400, "OUT_OF_SERVICE_AREA", "서울시 내 주소만 분석 가능합니다.")

    report_region_code = region_code or "UNKNOWN"
    cached_report = None
    if not payload.get("force_refresh", False):
        cached_report = await db.scalar(
            select(Report)
            .where(
                Report.user_id == user.user_id,
                Report.region_code == report_region_code,
                Report.created_at >= datetime.now(timezone.utc) - timedelta(hours=24),
            )
            .order_by(desc(Report.created_at))
            .limit(1)
        )
    if cached_report is not None:
        category_scores = _category_scores(cached_report)
        weighted_total_score = calculate_total_score(category_scores, weights_from_user(user))
        return {
            "status": "READY",
            "report_id": cached_report.report_id,
            "dong_code": cached_report.region_code,
            "dong_name": _dong_name(cached_report.address),
            "address": cached_report.address,
            "total_score": weighted_total_score,
            "cached": True,
            "analyzed_at": cached_report.created_at,
        }

    task_id = uuid4()
    await set_task_status(
        task_id,
        {
            "status": "PROCESSING",
            "progress": 0,
            "current_step": "분석 작업 대기 중",
            "completed_steps": [],
            "estimated_remaining_seconds": 15,
        },
    )
    background_tasks.add_task(run_mock_analysis, task_id, user.user_id, payload, report_region_code)

    return {
        "status": "PROCESSING",
        "task_id": task_id,
        "dong_code": report_region_code,
        "dong_name": _dong_name(payload["address"]),
        "address": payload["address"],
        "estimated_seconds": 15,
        "cached": False,
    }


async def run_mock_analysis(task_id: UUID, user_id: UUID, payload: dict, region_code: str) -> None:
    await set_task_status(
        task_id,
        {
            "status": "PROCESSING",
            "progress": 20,
            "current_step": "공공데이터 mock 수집 중",
            "completed_steps": ["작업 시작"],
            "estimated_remaining_seconds": 10,
        },
    )
    async with AsyncSessionLocal() as db:
        try:
            user = await db.get(User, user_id)
            if user is None:
                raise AppException(404, "USER_NOT_FOUND", "사용자를 찾을 수 없습니다.")

            analysis_data = await public_data_client.fetch_analysis_data(
                payload["lat"],
                payload["lng"],
                region_code,
            )
            report = _create_report_from_analysis_data(user, payload, region_code, analysis_data)
            db.add(report)
            await db.commit()
            await db.refresh(report)

            await set_task_status(
                task_id,
                {
                    "status": "COMPLETED",
                    "report_id": report.report_id,
                    "progress": 100,
                    "completed_steps": ["공공데이터 mock 수집", "점수 계산", "리포트 저장"],
                    "completed_at": datetime.now(timezone.utc),
                },
            )
        except Exception as exc:
            await db.rollback()
            logger.exception("분석 작업 실패: task_id=%s", task_id)
            await set_task_status(
                task_id,
                {
                    "status": "FAILED",
                    "progress": 100,
                    "error": {
                        "code": "ANALYSIS_FAILED",
                        "message": "분석 처리 중 오류가 발생했습니다.",
                        "details": str(exc),
                    },
                },
            )


async def get_status(task_id: UUID) -> dict:
    status = await get_task_status(task_id)
    if status is None:
        raise AppException(404, "TASK_NOT_FOUND", "분석 작업을 찾을 수 없습니다.")
    return status


async def get_owned_report(db: AsyncSession, user: User, report_id: UUID) -> Report:
    report = await db.get(Report, report_id)
    if report is None:
        raise ReportNotFoundError()
    if report.user_id != user.user_id:
        raise ForbiddenReportError()
    return report


async def analysis_response(db: AsyncSession, user: User, report_id: UUID) -> dict:
    report = await get_owned_report(db, user, report_id)
    category_scores = _category_scores(report)
    total_score = calculate_total_score(category_scores, weights_from_user(user))
    saved = await _is_saved(db, user, report.report_id)

    # 카테고리별 기본 데이터 구성
    categories_data = []
    for category, meta in REPORT_CATEGORIES.items():
        score = category_scores[category]
        categories_data.append({
            "type": category,
            "title": meta["title"],
            "score": score,
            "grade": grade_from_score(score),
            "summary": summary_for_score(score),  # Fallback 기본값
        })

    # AI 요약 병렬 생성 (종합 1 + 카테고리 5 = 6건)
    overall_task = generate_overall_summary(
        report.address, total_score, grade_from_score(total_score), categories_data,
    )
    category_tasks = [
        generate_category_summary(
            report.address, cat["title"], cat["score"], cat["grade"], [],
        )
        for cat in categories_data
    ]
    ai_results = await asyncio.gather(overall_task, *category_tasks, return_exceptions=True)

    # AI 결과 적용 (실패 시 기존 Fallback 유지)
    overall_ai = ai_results[0] if not isinstance(ai_results[0], Exception) else None
    overall_summary = overall_ai or summary_for_score(total_score)

    for i, cat in enumerate(categories_data):
        ai_cat = ai_results[i + 1] if not isinstance(ai_results[i + 1], Exception) else None
        if ai_cat:
            cat["summary"] = ai_cat

    return {
        "report_id": report.report_id,
        "address": report.address,
        "dong_code": report.region_code,
        "total_score": total_score,
        "grade": grade_from_score(total_score),
        "summary": overall_summary,
        "score_source": {"base_score_cached": True, "weight_applied": True},
        "categories": categories_data,
        "saved": saved,
    }


async def detail_response(db: AsyncSession, user: User, report_id: UUID, category: str) -> dict:
    report = await get_owned_report(db, user, report_id)
    handlers = {
        "flood": flood.get_flood_detail,
        "security": security.get_security_detail,
        "medical": medical.get_medical_detail,
        "noise": noise.get_noise_detail,
        "congestion": congestion.get_congestion_detail,
    }
    data = handlers[category](report)
    meta = REPORT_CATEGORIES[category]
    score = data["score"]

    # AI 카테고리 요약 생성 (indicators 정보를 함께 전달)
    ai_summary = await generate_category_summary(
        report.address, meta["title"], score, grade_from_score(score), data["indicators"],
    )

    return {
        "report_id": report.report_id,
        "address": report.address,
        "region_code": report.region_code,
        "category": category,
        "title": meta["title"],
        "score": score,
        "base_score": data.get("base_score", score),
        "grade": grade_from_score(score),
        "summary": ai_summary or data["summary"],  # AI 실패 시 기존 Fallback
        "indicators": data["indicators"],
        "visualization": data.get("visualization"),
        "data_source": data["data_source"],
    }


def category_scores(report: Report) -> dict[str, int]:
    return _category_scores(report)


def _category_scores(report: Report) -> dict[str, int]:
    return {
        "flood": flood.calculate_flood_score(report),
        "security": security.calculate_security_score(report),
        "medical": medical.calculate_medical_score(report),
        "noise": noise.calculate_noise_score(report),
        "congestion": congestion.calculate_congestion_score(report),
    }


async def _is_saved(db: AsyncSession, user: User, report_id: UUID) -> bool:
    bookmark = await db.scalar(
        select(Bookmark).where(and_(Bookmark.user_id == user.user_id, Bookmark.report_id == report_id))
    )
    return bookmark is not None


def _create_report_from_analysis_data(user: User, payload: dict, region_code: str, analysis_data: dict) -> Report:
    report = Report(
        user_id=user.user_id,
        address=payload["address"],
        address_detail=payload.get("road_addr") or payload.get("jibun_addr"),
        region_code=region_code,
        lat=payload["lat"],
        lng=payload["lng"],
        cctv_count=analysis_data["cctv_count"],
        cctv_growth=analysis_data["cctv_growth"],
        crime_count=analysis_data["crime_count"],
        safepath_score=analysis_data["safepath_score"],
        police_count=analysis_data["police_count"],
        police_pop_ratio=analysis_data["police_pop_ratio"],
        light_blind_ratio=analysis_data["light_blind_ratio"],
        safety_map=analysis_data.get("safety_map"),
        impervious_ratio=analysis_data["impervious_ratio"],
        pump_cap=analysis_data["pump_cap"],
        flood_map=analysis_data.get("flood_map"),
        noise_pub_density=analysis_data["noise_pub_density"],
        noise_complaint=analysis_data["noise_complaint"],
        noise_db=analysis_data["noise_db"],
        road_noise=analysis_data["road_noise"],
        aircraft_noise=analysis_data["aircraft_noise"],
        rail_noise=analysis_data["rail_noise"],
        noise_hourly=analysis_data["noise_hourly"],
        noise_table=analysis_data.get("noise_table"),
        night_clinic=analysis_data["night_clinic"],
        pharmacy_count=analysis_data["pharmacy_count"],
        medical_staff=analysis_data["medical_staff"],
        medic_map=analysis_data.get("medic_map"),
        congestion_data=analysis_data["congestion_data"],
    )
    scores = _category_scores(report)
    report.flood_score = scores["flood"]
    report.security_score = scores["security"]
    report.medical_score = scores["medical"]
    report.noise_score = scores["noise"]
    report.congestion_score = scores["congestion"]
    report.total_score = _base_total_score(scores)
    return report


def _base_total_score(scores: dict[str, int]) -> int:
    return round(sum(scores.values()) / len(scores))


def _is_seoul_location(dong_code: str | None, *addresses: str | None) -> bool:
    if dong_code:
        return dong_code.startswith("11")
    return any(address and ("서울" in address or "Seoul" in address) for address in addresses)


def _dong_name(address: str) -> str:
    return next((part for part in address.split() if part.endswith("동")), "")
