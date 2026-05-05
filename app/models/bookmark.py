import uuid
from sqlalchemy import Column, ForeignKey, func, Index, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID, TIMESTAMP
from sqlalchemy.orm import relationship

from app.db.base import Base

class Bookmark(Base):
    __tablename__ = "bookmarks"

    bookmark_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    report_id = Column(UUID(as_uuid=True), ForeignKey("reports.report_id", ondelete="CASCADE"), nullable=False)

    # Relationships
    user = relationship("User", back_populates="bookmarks")
    report = relationship("Report", back_populates="bookmarks")

    __table_args__ = (
        UniqueConstraint('user_id', 'report_id', name='bookmarks_unique_user_report'),
        Index("idx_bookmarks_user_id", "user_id"),
        Index("idx_bookmarks_report_id", "report_id"),
    )
