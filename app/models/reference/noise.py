from sqlalchemy import Column, Float, Index, Integer, String
from geoalchemy2 import Geometry

from app.db.base import Base


class RefNoisePub(Base):
    __tablename__ = "ref_noise_pub"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=True)
    address = Column(String, nullable=True)
    lat = Column(Float, nullable=False)
    lon = Column(Float, nullable=False)
    geom = Column(Geometry("POINT", srid=4326), nullable=False)
    raw_score = Column(Float, nullable=True)

    __table_args__ = (Index("idx_ref_noise_pub_geom", "geom", postgresql_using="gist"),)


class RefNoiseRoad(Base):
    __tablename__ = "ref_noise_road"

    id = Column(Integer, primary_key=True, autoincrement=True)
    its_link_id = Column(String, nullable=True, index=True)
    road_name = Column(String, nullable=True)
    region = Column(String, nullable=True, index=True)
    raw_score = Column(Float, nullable=True)


class RefNoiseRail(Base):
    __tablename__ = "ref_noise_rail"

    id = Column(Integer, primary_key=True, autoincrement=True)
    from_station = Column(String, nullable=True)
    from_line = Column(String, nullable=True)
    to_station = Column(String, nullable=True)
    to_line = Column(String, nullable=True)
    distance = Column(Float, nullable=True)
    raw_score = Column(Float, nullable=True)


class RefNoiseComplaint(Base):
    __tablename__ = "ref_noise_complaint"

    id = Column(Integer, primary_key=True, autoincrement=True)
    gu_name = Column(String, nullable=False, unique=True, index=True)
    raw_score = Column(Float, nullable=True)


class RefNoiseMeasurement(Base):
    __tablename__ = "ref_noise_measurement"

    id = Column(Integer, primary_key=True, autoincrement=True)
    station = Column(String, nullable=True, index=True)
    address = Column(String, nullable=True)
    land_use = Column(String, nullable=True)
    leq = Column(Float, nullable=True)
    raw_score = Column(Float, nullable=True)


class RefNoiseAircraft(Base):
    __tablename__ = "ref_noise_aircraft"

    id = Column(Integer, primary_key=True, autoincrement=True)
    station = Column(String, nullable=True, index=True)
    raw_score = Column(Float, nullable=True)


class RefNoiseHourly(Base):
    __tablename__ = "ref_noise_hourly"

    id = Column(Integer, primary_key=True, autoincrement=True)
    station = Column(String, nullable=True, index=True)
    hour = Column(String, nullable=True)
    raw_score = Column(Float, nullable=True)


class RefNoiseIdwGrid(Base):
    __tablename__ = "ref_noise_idw_grid"

    id = Column(Integer, primary_key=True, autoincrement=True)
    grid_lat = Column(Float, nullable=False)
    grid_lon = Column(Float, nullable=False)
    estimated_db = Column(Float, nullable=False)
    geom = Column(Geometry("POINT", srid=4326), nullable=False)

    __table_args__ = (Index("idx_ref_noise_idw_grid_geom", "geom", postgresql_using="gist"),)


class RefNoiseLdenPoint(Base):
    __tablename__ = "ref_noise_lden_point"

    id = Column(Integer, primary_key=True, autoincrement=True)
    station = Column(String, nullable=True, index=True)
    lat = Column(Float, nullable=False)
    lon = Column(Float, nullable=False)
    radius_m = Column(Float, nullable=True)
    raw_score = Column(Float, nullable=True)
    geom = Column(Geometry("POINT", srid=4326), nullable=False)

    __table_args__ = (Index("idx_ref_noise_lden_point_geom", "geom", postgresql_using="gist"),)


class RefNoiseTrafficPoint(Base):
    __tablename__ = "ref_noise_traffic_point"

    id = Column(Integer, primary_key=True, autoincrement=True)
    point_no = Column(String, nullable=True, index=True)
    point_name = Column(String, nullable=True)
    daily_traffic = Column(Float, nullable=True)
    night_traffic = Column(Float, nullable=True)
    lat = Column(Float, nullable=False)
    lon = Column(Float, nullable=False)
    raw_score = Column(Float, nullable=True)
    geom = Column(Geometry("POINT", srid=4326), nullable=False)

    __table_args__ = (Index("idx_ref_noise_traffic_point_geom", "geom", postgresql_using="gist"),)
