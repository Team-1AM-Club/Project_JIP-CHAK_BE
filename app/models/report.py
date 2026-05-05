import uuid
from sqlalchemy import Column, String, Integer, SmallInteger, Float, ForeignKey, func, Index, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID, TIMESTAMP, ARRAY, JSONB
from sqlalchemy.orm import relationship

from app.db.base import Base

class Report(Base):
    __tablename__ = "reports"

    report_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    address = Column(String, nullable=False)
    address_detail = Column(String, nullable=True)
    region_code = Column(String, nullable=False)
    lat = Column(Float, nullable=False)
    lng = Column(Float, nullable=False)

    # 치안 (security)
    criminal_occur = Column(ARRAY(Integer), nullable=False, server_default='{}')
    cctv_count = Column(Integer, nullable=False, default=0)
    lamp_count = Column(Integer, nullable=False, default=0)
    police_dist = Column(Float, nullable=False, default=0.0)
    safety_map = Column(JSONB, nullable=True)

    # 침수 (flood)
    altitude = Column(Float, nullable=False, default=0.0)
    flood_hist = Column(Integer, nullable=False, default=0)
    low_ratio = Column(SmallInteger, nullable=False, default=0)
    pump_cap = Column(SmallInteger, nullable=False, default=0)
    river_dist = Column(Integer, nullable=False, default=0)
    flood_map = Column(JSONB, nullable=True)

    # 소음 (noise)
    road_noise = Column(SmallInteger, nullable=False, default=0)
    noise_report = Column(Integer, nullable=False, default=0)
    ent_place = Column(Integer, nullable=False, default=0)
    train_noise = Column(Integer, nullable=False, default=0)
    noise_table = Column(JSONB, nullable=True)

    # 의료 (medical)
    medic_dist = Column(Integer, nullable=False, default=0)
    nightopen_count = Column(Integer, nullable=False, default=0)
    emeropen_count = Column(Integer, nullable=False, default=0)
    emer_cap = Column(Integer, nullable=False, default=0)
    doctor_ratio = Column(Float, nullable=False, default=0.0)
    medic_map = Column(JSONB, nullable=True)

    # 혼잡도 (congestion)
    congestion_data = Column(JSONB, nullable=True)

    # 리스크 점수 캐시 (score caching)
    security_score = Column(SmallInteger, nullable=True)
    flood_score = Column(SmallInteger, nullable=True)
    noise_score = Column(SmallInteger, nullable=True)
    medical_score = Column(SmallInteger, nullable=True)
    congestion_score = Column(SmallInteger, nullable=True)
    total_score = Column(SmallInteger, nullable=True)

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)

    # Relationships
    user = relationship("User", back_populates="reports")
    bookmarks = relationship("Bookmark", back_populates="report", cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint(
            "(security_score IS NULL OR security_score BETWEEN 0 AND 100) AND "
            "(flood_score IS NULL OR flood_score BETWEEN 0 AND 100) AND "
            "(noise_score IS NULL OR noise_score BETWEEN 0 AND 100) AND "
            "(medical_score IS NULL OR medical_score BETWEEN 0 AND 100) AND "
            "(congestion_score IS NULL OR congestion_score BETWEEN 0 AND 100) AND "
            "(total_score IS NULL OR total_score BETWEEN 0 AND 100)",
            name="reports_score_range_check"
        ),
        Index("idx_reports_user_id", "user_id"),
        Index("idx_reports_user_created_at", "user_id", "created_at"),  # Using string for created_at in index to avoid referencing column property inside table_args
        Index("idx_reports_region_code", "region_code"),
    )
