from sqlalchemy import Column, Float, Index, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from geoalchemy2 import Geometry

from app.db.base import Base


class RefBusStop(Base):
    __tablename__ = "ref_bus_stop"

    id = Column(Integer, primary_key=True, autoincrement=True)
    node_id = Column(String, nullable=True, index=True)
    ars_id = Column(String, nullable=True)
    stop_name = Column(String, nullable=True)
    stop_type = Column(String, nullable=True)
    lat = Column(Float, nullable=False)
    lon = Column(Float, nullable=False)
    geom = Column(Geometry("POINT", srid=4326), nullable=False)
    daily_avg_usage = Column(Float, nullable=True)
    raw_score = Column(Float, nullable=True)

    __table_args__ = (Index("idx_ref_bus_stop_geom", "geom", postgresql_using="gist"),)


class RefBusHourly(Base):
    __tablename__ = "ref_bus_hourly"

    id = Column(Integer, primary_key=True, autoincrement=True)
    node_id = Column(String, nullable=True, index=True)
    stop_name = Column(String, nullable=True)
    lat = Column(Float, nullable=False)
    lon = Column(Float, nullable=False)
    geom = Column(Geometry("POINT", srid=4326), nullable=False)
    hourly_pop = Column(JSONB, nullable=True)

    __table_args__ = (Index("idx_ref_bus_hourly_geom", "geom", postgresql_using="gist"),)


class RefSubwayCongestion(Base):
    __tablename__ = "ref_subway_congestion"

    id = Column(Integer, primary_key=True, autoincrement=True)
    station_name = Column(String, nullable=False, unique=True, index=True)
    peak_max_congestion = Column(Float, nullable=True)
    raw_score = Column(Float, nullable=True)


class RefFloatingPopulation(Base):
    __tablename__ = "ref_floating_pop"

    id = Column(Integer, primary_key=True, autoincrement=True)
    dong_code = Column(String, nullable=False, unique=True, index=True)
    total_pop = Column(Float, nullable=True)
    raw_score = Column(Float, nullable=True)
