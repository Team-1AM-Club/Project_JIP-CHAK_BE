# 불완전: 저장 매물 로직은 구현됐지만 실제 PostgreSQL 통합 테스트가 필요함.
from uuid import UUID

from sqlalchemy import and_, case, delete, func, literal, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import grade_from_score, score_status
from app.core.exceptions import AppException, ForbiddenReportError, ReportNotFoundError
from app.models.bookmark import Bookmark
from app.models.report import Report
from app.models.user import User


async def list_bookmarks(db: AsyncSession, user: User, status: str, page: int, size: int) -> dict:
    if status not in {"ALL", "SAFE", "CAUTION", "RISK"}:
        raise AppException(400, "INVALID_INPUT_VALUE", "유효하지 않은 필터 상태입니다.")
    if page < 1 or size < 1:
        raise AppException(400, "INVALID_INPUT_VALUE", "페이지 값이 올바르지 않습니다.")

    weighted_score = _weighted_score_expression(user)
    base_filter = Bookmark.user_id == user.user_id
    count_query = (
        select(
            func.count().label("total_cnt"),
            func.coalesce(func.sum(case((weighted_score >= 80, 1), else_=0)), 0).label("safe_cnt"),
            func.coalesce(
                func.sum(case((and_(weighted_score >= 60, weighted_score < 80), 1), else_=0)),
                0,
            ).label("caution_cnt"),
            func.coalesce(func.sum(case((weighted_score < 60, 1), else_=0)), 0).label("risk_cnt"),
        )
        .select_from(Bookmark)
        .join(Report, Bookmark.report_id == Report.report_id)
        .where(base_filter)
    )
    counts_row = (await db.execute(count_query)).one()

    query = (
        select(Bookmark, Report, weighted_score.label("weighted_score"))
        .join(Report, Bookmark.report_id == Report.report_id)
        .where(base_filter)
        .order_by(Bookmark.created_at.desc())
        .offset((page - 1) * size)
        .limit(size)
    )
    if status != "ALL":
        query = query.where(_status_filter(status, weighted_score))

    rows = (await db.execute(query)).all()
    total_elements = _count_for_status(counts_row, status)
    return {
        "filter_counts": {
            "total_cnt": int(counts_row.total_cnt),
            "safe_cnt": int(counts_row.safe_cnt),
            "caution_cnt": int(counts_row.caution_cnt),
            "risk_cnt": int(counts_row.risk_cnt),
        },
        "content": [_bookmark_item(bookmark, report, weighted_score) for bookmark, report, weighted_score in rows],
        "page": page,
        "size": size,
        "total_elements": total_elements,
    }


async def create_bookmark(db: AsyncSession, user: User, property_id: UUID, report_id: UUID | None) -> dict:
    target_report_id = report_id or property_id
    report = await db.get(Report, target_report_id)
    if report is None:
        raise ReportNotFoundError()
    if report.user_id != user.user_id:
        raise ForbiddenReportError()

    exists = await db.scalar(
        select(Bookmark).where(and_(Bookmark.user_id == user.user_id, Bookmark.report_id == target_report_id))
    )
    if exists is not None:
        raise AppException(409, "PROPERTY_ALREADY_BOOKMARKED", "이미 저장된 매물입니다.")

    db.add(Bookmark(user_id=user.user_id, report_id=target_report_id))
    await db.commit()
    return {"property_id": property_id, "report_id": target_report_id, "bookmarked": True}


async def delete_bookmark(db: AsyncSession, user: User, report_id: UUID) -> dict:
    result = await db.execute(
        delete(Bookmark).where(and_(Bookmark.user_id == user.user_id, Bookmark.report_id == report_id))
    )
    if result.rowcount == 0:
        raise AppException(404, "PROPERTY_NOT_BOOKMARKED", "저장되지 않은 매물입니다.")
    await db.commit()
    return {"property_id": report_id, "bookmarked": False}


async def is_bookmarked(db: AsyncSession, user: User, report_id: UUID) -> bool:
    count = await db.scalar(
        select(func.count()).select_from(Bookmark).where(
            and_(Bookmark.user_id == user.user_id, Bookmark.report_id == report_id)
        )
    )
    return bool(count)


def _bookmark_item(bookmark: Bookmark, report: Report, weighted_score: int) -> dict:
    weighted_score = int(weighted_score or 0)
    status = score_status(weighted_score)
    grade = grade_from_score(weighted_score)
    return {
        "property_id": report.report_id,
        "report_id": report.report_id,
        "address": report.address,
        "description": report.address_detail,
        "score": weighted_score,
        "grade": grade,
        "score_status": status,
        "tags": [grade],
        "bookmarked": True,
        "saved_at": bookmark.created_at,
    }


def _status_filter(status: str, weighted_score):
    if status == "SAFE":
        return weighted_score >= 80
    if status == "CAUTION":
        return and_(weighted_score >= 60, weighted_score < 80)
    return weighted_score < 60


def _count_for_status(counts_row, status: str) -> int:
    if status == "SAFE":
        return int(counts_row.safe_cnt)
    if status == "CAUTION":
        return int(counts_row.caution_cnt)
    if status == "RISK":
        return int(counts_row.risk_cnt)
    return int(counts_row.total_cnt)


def _weighted_score_expression(user: User):
    security_weight = literal(user.security_weight)
    noise_weight = literal(user.noise_weight)
    medical_weight = literal(user.medical_weight)
    flood_weight = literal(user.flood_weight)
    congestion_weight = literal(user.congestion_weight)

    return func.round(
        (
            func.coalesce(Report.security_score, literal(0)) * security_weight
            + func.coalesce(Report.noise_score, literal(0)) * noise_weight
            + func.coalesce(Report.medical_score, literal(0)) * medical_weight
            + func.coalesce(Report.flood_score, literal(0)) * flood_weight
            + func.coalesce(Report.congestion_score, literal(0)) * congestion_weight
        )
        / 100
    )
