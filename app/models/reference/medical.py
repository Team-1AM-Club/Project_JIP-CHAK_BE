from sqlalchemy import Column, Float, Index, Integer, String
from geoalchemy2 import Geometry

from app.db.base import Base


class RefNightClinic(Base):
    __tablename__ = "ref_night_clinic"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=True)
    gu_name = Column(String, nullable=True, index=True)
    dong_name = Column(String, nullable=True, index=True)
    lat = Column(Float, nullable=False)
    lon = Column(Float, nullable=False)
    geom = Column(Geometry("POINT", srid=4326), nullable=False)
    raw_score = Column(Float, nullable=True)

    __table_args__ = (Index("idx_ref_night_clinic_geom", "geom", postgresql_using="gist"),)


class RefPharmacy(Base):
    __tablename__ = "ref_pharmacy"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=True)
    gu_name = Column(String, nullable=True, index=True)
    dong_name = Column(String, nullable=True, index=True)
    lat = Column(Float, nullable=False)
    lon = Column(Float, nullable=False)
    geom = Column(Geometry("POINT", srid=4326), nullable=False)
    raw_score = Column(Float, nullable=True)

    __table_args__ = (Index("idx_ref_pharmacy_geom", "geom", postgresql_using="gist"),)


class RefHealthDong(Base):
    __tablename__ = "ref_health_dong"

    id = Column(Integer, primary_key=True, autoincrement=True)
    gu_name = Column(String, nullable=True, index=True)
    dong_name = Column(String, nullable=True, index=True)
    night_clinic_count = Column(Float, nullable=True)
    raw_score_clinic = Column(Float, nullable=True)
    pharmacy_count = Column(Float, nullable=True)
    raw_score_pharmacy = Column(Float, nullable=True)


class RefHealthWorkforce(Base):
    __tablename__ = "ref_health_workforce"

    id = Column(Integer, primary_key=True, autoincrement=True)
    gu_name = Column(String, nullable=False, unique=True, index=True)
    nurse_count = Column(Integer, nullable=True)
    specialist_count = Column(Integer, nullable=True)
    raw_score = Column(Float, nullable=True)
