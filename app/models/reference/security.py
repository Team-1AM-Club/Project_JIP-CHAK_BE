from sqlalchemy import Boolean, Column, Float, Index, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from geoalchemy2 import Geometry

from app.db.base import Base


class RefCctv(Base):
    __tablename__ = "ref_cctv"

    id = Column(Integer, primary_key=True, autoincrement=True)
    agency = Column(String, nullable=True)
    address = Column(String, nullable=True)
    lat = Column(Float, nullable=False)
    lon = Column(Float, nullable=False)
    geom = Column(Geometry("POINT", srid=4326), nullable=False)
    raw_score = Column(Float, nullable=True)

    __table_args__ = (Index("idx_ref_cctv_geom", "geom", postgresql_using="gist"),)


class RefLightBlind(Base):
    __tablename__ = "ref_light_blind"

    id = Column(Integer, primary_key=True, autoincrement=True)
    mgmt_no = Column(String, nullable=True)
    lat = Column(Float, nullable=False)
    lon = Column(Float, nullable=False)
    geom = Column(Geometry("POINT", srid=4326), nullable=False)
    dist_to_nearest = Column(Float, nullable=True)
    is_blind = Column(Boolean, nullable=False, default=False)
    raw_score = Column(Float, nullable=True)

    __table_args__ = (Index("idx_ref_light_blind_geom", "geom", postgresql_using="gist"),)


class RefPolice(Base):
    __tablename__ = "ref_police"

    id = Column(Integer, primary_key=True, autoincrement=True)
    station = Column(String, nullable=True)
    office_name = Column(String, nullable=True)
    category = Column(String, nullable=True)
    address = Column(String, nullable=True)
    lat = Column(Float, nullable=True)
    lon = Column(Float, nullable=True)
    geom = Column(Geometry("POINT", srid=4326), nullable=True)
    raw_score = Column(Float, nullable=True)

    __table_args__ = (Index("idx_ref_police_geom", "geom", postgresql_using="gist"),)


class RefCrime(Base):
    __tablename__ = "ref_crime"

    id = Column(Integer, primary_key=True, autoincrement=True)
    gu_name = Column(String, nullable=False, unique=True, index=True)
    raw_score = Column(Float, nullable=True)
    detail_json = Column(JSONB, nullable=True)


class RefPolicePopulation(Base):
    __tablename__ = "ref_police_pop"

    id = Column(Integer, primary_key=True, autoincrement=True)
    gu_name = Column(String, nullable=False, index=True)
    dong_code = Column(String, nullable=True, index=True)
    population = Column(Float, nullable=True)
    police_count = Column(Integer, nullable=True)
    raw_score = Column(Float, nullable=True)


class RefCctvGrowth(Base):
    __tablename__ = "ref_cctv_growth"

    id = Column(Integer, primary_key=True, autoincrement=True)
    gu_name = Column(String, nullable=False, unique=True, index=True)
    count_2015 = Column(Integer, nullable=True)
    count_2025 = Column(Integer, nullable=True)
    growth_rate = Column(Float, nullable=True)
    raw_score = Column(Float, nullable=True)
    detail_json = Column(JSONB, nullable=True)


class RefSafePath(Base):
    __tablename__ = "ref_safepath"

    id = Column(Integer, primary_key=True, autoincrement=True)
    region_code = Column(String, nullable=True, index=True)
    length_m = Column(Float, nullable=True)
    raw_score = Column(Float, nullable=True)
