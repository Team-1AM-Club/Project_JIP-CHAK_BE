# 불완전: 리포트 API contract는 구현됐지만 분석 데이터는 실제 공공데이터 대신 mock interface를 사용함.
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.common import success_response
from app.schemas.report import AnalysisRequest
from app.services import compare_service, report_service

router = APIRouter(prefix="/reports", tags=["reports"])


@router.post("")
async def request_analysis(
    request: AnalysisRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await report_service.request_analysis(db, current_user, request.model_dump(), background_tasks)
    return success_response(result["data"], status=result["status"])


@router.get("/status/{task_id}")
async def get_status(task_id: UUID):
    return success_response(await report_service.get_status(task_id))


@router.get("/compare")
async def compare(
    report_ids: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    parsed_ids = compare_service.parse_report_ids(report_ids)
    return success_response(await compare_service.compare_reports(db, current_user, parsed_ids))


@router.get("/{reportId}/analysis")
async def get_analysis(
    reportId: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return success_response(await report_service.analysis_response(db, current_user, reportId))


@router.get("/{reportId}/flood")
async def get_flood(reportId: UUID, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    return success_response(await report_service.detail_response(db, current_user, reportId, "flood"))


@router.get("/{reportId}/security")
async def get_security(reportId: UUID, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    return success_response(await report_service.detail_response(db, current_user, reportId, "security"))


@router.get("/{reportId}/medical")
async def get_medical(reportId: UUID, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    return success_response(await report_service.detail_response(db, current_user, reportId, "medical"))


@router.get("/{reportId}/noise")
async def get_noise(reportId: UUID, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    return success_response(await report_service.detail_response(db, current_user, reportId, "noise"))


@router.get("/{reportId}/congestion")
async def get_congestion(reportId: UUID, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    return success_response(await report_service.detail_response(db, current_user, reportId, "congestion"))
