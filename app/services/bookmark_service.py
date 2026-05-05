# 불완전: 저장 매물 로직은 구현됐지만 실제 PostgreSQL에서 join, unique constraint, 삭제 rowcount 검증이 필요함.
from uuid import UUID

from sqlalchemy import and_, delete, func, select
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

    rows = (
        await db.execute(
            select(Bookmark, Report)
            .join(Report, Bookmark.report_id == Report.report_id)
            .where(Bookmark.user_id == user.user_id)
            .order_by(Bookmark.created_at.desc())
        )
    ).all()

    items = [_bookmark_item(bookmark, report) for bookmark, report in rows]
    counts = _filter_counts(items)
    filtered = items if status == "ALL" else [item for item in items if item["score_status"] == status]
    start = (page - 1) * size
    return {
        "filter_counts": counts,
        "content": filtered[start : start + size],
        "page": page,
        "size": size,
        "total_elements": len(filtered),
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


def _bookmark_item(bookmark: Bookmark, report: Report) -> dict:
    status = score_status(report.total_score)
    grade = grade_from_score(report.total_score)
    return {
        "property_id": report.report_id,
        "report_id": report.report_id,
        "address": report.address,
        "description": report.address_detail,
        "score": report.total_score,
        "grade": grade,
        "score_status": status,
        "tags": [grade],
        "bookmarked": True,
        "saved_at": bookmark.created_at,
    }


def _filter_counts(items: list[dict]) -> dict[str, int]:
    return {
        "total_cnt": len(items),
        "safe_cnt": sum(item["score_status"] == "SAFE" for item in items),
        "caution_cnt": sum(item["score_status"] == "CAUTION" for item in items),
        "risk_cnt": sum(item["score_status"] == "RISK" for item in items),
    }
