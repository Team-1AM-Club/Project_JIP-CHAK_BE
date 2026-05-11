from sqlalchemy import Column, Float, Index, Integer, String
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
