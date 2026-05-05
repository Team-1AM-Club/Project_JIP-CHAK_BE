import uuid
from sqlalchemy import Column, String, Boolean, SmallInteger, CheckConstraint, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID, TIMESTAMP
from sqlalchemy.orm import relationship

from app.db.base import Base

class User(Base):
    __tablename__ = "users"

    user_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_name = Column(String, nullable=False)
    email = Column(String, nullable=False, unique=True)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    user_type = Column(String, nullable=False, default='Single')
    
    # OAuth
    provider = Column(String, nullable=False, default='GOOGLE')
    provider_id = Column(String, nullable=False)

    # 앱 설정
    noti_enabled = Column(Boolean, nullable=False, default=True)
    dark_mode = Column(String, nullable=False, default='SYSTEM')

    # 사용자 가중치 설정
    flood_weight = Column(SmallInteger, nullable=False, default=20)
    security_weight = Column(SmallInteger, nullable=False, default=20)
    noise_weight = Column(SmallInteger, nullable=False, default=20)
    medical_weight = Column(SmallInteger, nullable=False, default=20)
    congestion_weight = Column(SmallInteger, nullable=False, default=20)

    # Relationships
    refresh_tokens = relationship("RefreshToken", back_populates="user", cascade="all, delete-orphan")
    reports = relationship("Report", back_populates="user", cascade="all, delete-orphan")
    bookmarks = relationship("Bookmark", back_populates="user", cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint("user_type IN ('Single', 'Newlyweds', 'Dependents')", name="users_user_type_check"),
        CheckConstraint("dark_mode IN ('SYSTEM', 'DARK', 'LIGHT')", name="users_dark_mode_check"),
        UniqueConstraint('provider', 'provider_id', name='users_provider_unique'),
        CheckConstraint(
            "flood_weight BETWEEN 0 AND 100 AND "
            "security_weight BETWEEN 0 AND 100 AND "
            "noise_weight BETWEEN 0 AND 100 AND "
            "medical_weight BETWEEN 0 AND 100 AND "
            "congestion_weight BETWEEN 0 AND 100",
            name="users_weights_range_check"
        ),
        CheckConstraint(
            "flood_weight + security_weight + noise_weight + medical_weight + congestion_weight = 100",
            name="users_weights_sum_check"
        ),
    )
