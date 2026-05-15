from sqlalchemy import Boolean, Column, Float, Index, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from geoalchemy2 import Geometry

from app.db.base import Base


class RefFloodTrace(Base):
    __tablename__ = "ref_flood_trace"

    id = Column(Integer, primary_key=True, autoincrement=True)
    geom = Column(Geometry("MULTIPOLYGON", srid=4326), nullable=False)
    properties = Column(JSONB, nullable=True)

    __table_args__ = (Index("idx_ref_flood_trace_geom", "geom", postgresql_using="gist"),)


class RefFloodPump(Base):
    __tablename__ = "ref_flood_pump"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=True)
    address = Column(String, nullable=True)
    max_capacity = Column(Float, nullable=True)
    lat = Column(Float, nullable=False)
    lon = Column(Float, nullable=False)
    geom = Column(Geometry("POINT", srid=4326), nullable=False)
    raw_score = Column(Float, nullable=True)

    __table_args__ = (Index("idx_ref_flood_pump_geom", "geom", postgresql_using="gist"),)


class RefImpervious(Base):
    __tablename__ = "ref_impervious"

    id = Column(Integer, primary_key=True, autoincrement=True)
    gu_name = Column(String, nullable=False, unique=True, index=True)
    impervious_ratio = Column(Float, nullable=True)
    raw_score = Column(Float, nullable=True)


class RefFloodDefense(Base):
    __tablename__ = "ref_flood_defense"

    id = Column(Integer, primary_key=True, autoincrement=True)
    gu_name = Column(String, nullable=False, unique=True, index=True)
    avg_elevation_m = Column(Float, nullable=True)
    num_stations = Column(Float, nullable=True)
    total_pump_m3 = Column(Float, nullable=True)
    total_basin = Column(Float, nullable=True)
    pump_efficiency = Column(Float, nullable=True)
    max_freq = Column(Float, nullable=True)
    avg_coverage_rate = Column(Float, nullable=True)
    imperv_proxy = Column(Float, nullable=True)
    n_buildings = Column(Integer, nullable=True)
    score_elevation = Column(Float, nullable=True)
    score_pump = Column(Float, nullable=True)
    score_imperv = Column(Float, nullable=True)
    raw_score = Column(Float, nullable=True)
    contour_line_count = Column(Integer, nullable=True)
    score_contour = Column(Float, nullable=True)


class RefFloodTraceSummary(Base):
    __tablename__ = "ref_flood_trace_summary"

    id = Column(Integer, primary_key=True, autoincrement=True)
    gu_name = Column(String, nullable=False, unique=True, index=True)
    flood_count = Column(Float, nullable=True)
    total_flood_area = Column(Float, nullable=True)
    mean_flood_area = Column(Float, nullable=True)
    mean_flood_depth = Column(Float, nullable=True)
    max_flood_depth = Column(Float, nullable=True)
    raw_score = Column(Float, nullable=True)
    data_available = Column(Boolean, nullable=True)
    data_year = Column(Integer, nullable=True)


class RefFloodTracePoint(Base):
    __tablename__ = "ref_flood_trace_point"

    id = Column(Integer, primary_key=True, autoincrement=True)
    gu_name = Column(String, nullable=False, index=True)
    address = Column(String, nullable=True)
    flood_year = Column(Integer, nullable=True)
    flood_area_m2 = Column(Float, nullable=True)
    flood_depth_cm = Column(Float, nullable=True)
    flood_type = Column(String, nullable=True)
    lat = Column(Float, nullable=True)
    lon = Column(Float, nullable=True)
    geom = Column(Geometry("POINT", srid=4326), nullable=True)
    is_outlier_area = Column(Boolean, nullable=True)
    flood_area_m2_clipped = Column(Float, nullable=True)
    raw_score = Column(Float, nullable=True)

    __table_args__ = (Index("idx_ref_flood_trace_point_geom", "geom", postgresql_using="gist"),)
