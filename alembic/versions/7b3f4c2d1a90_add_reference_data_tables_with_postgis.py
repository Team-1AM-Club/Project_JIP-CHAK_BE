"""add reference data tables with PostGIS

Revision ID: 7b3f4c2d1a90
Revises: 2950295a86a3
Create Date: 2026-05-12 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op


revision: str = "7b3f4c2d1a90"
down_revision: Union[str, Sequence[str], None] = "2950295a86a3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis;")
    for statement in """
        CREATE TABLE ref_cctv (
            id SERIAL PRIMARY KEY,
            agency VARCHAR,
            address VARCHAR,
            lat DOUBLE PRECISION NOT NULL,
            lon DOUBLE PRECISION NOT NULL,
            geom geometry(POINT, 4326) NOT NULL,
            raw_score DOUBLE PRECISION
        );
        CREATE INDEX idx_ref_cctv_geom ON ref_cctv USING GIST (geom);

        CREATE TABLE ref_light_blind (
            id SERIAL PRIMARY KEY,
            mgmt_no VARCHAR,
            lat DOUBLE PRECISION NOT NULL,
            lon DOUBLE PRECISION NOT NULL,
            geom geometry(POINT, 4326) NOT NULL,
            dist_to_nearest DOUBLE PRECISION,
            is_blind BOOLEAN NOT NULL DEFAULT FALSE,
            raw_score DOUBLE PRECISION
        );
        CREATE INDEX idx_ref_light_blind_geom ON ref_light_blind USING GIST (geom);

        CREATE TABLE ref_police (
            id SERIAL PRIMARY KEY,
            station VARCHAR,
            office_name VARCHAR,
            category VARCHAR,
            address VARCHAR,
            lat DOUBLE PRECISION,
            lon DOUBLE PRECISION,
            geom geometry(POINT, 4326),
            raw_score DOUBLE PRECISION
        );
        CREATE INDEX idx_ref_police_geom ON ref_police USING GIST (geom);

        CREATE TABLE ref_crime (
            id SERIAL PRIMARY KEY,
            gu_name VARCHAR NOT NULL UNIQUE,
            raw_score DOUBLE PRECISION
        );
        CREATE INDEX ix_ref_crime_gu_name ON ref_crime (gu_name);

        CREATE TABLE ref_police_pop (
            id SERIAL PRIMARY KEY,
            gu_name VARCHAR NOT NULL,
            dong_code VARCHAR,
            population DOUBLE PRECISION,
            police_count INTEGER,
            raw_score DOUBLE PRECISION
        );
        CREATE INDEX ix_ref_police_pop_gu_name ON ref_police_pop (gu_name);
        CREATE INDEX ix_ref_police_pop_dong_code ON ref_police_pop (dong_code);

        CREATE TABLE ref_cctv_growth (
            id SERIAL PRIMARY KEY,
            gu_name VARCHAR NOT NULL UNIQUE,
            count_2015 INTEGER,
            count_2025 INTEGER,
            growth_rate DOUBLE PRECISION,
            raw_score DOUBLE PRECISION
        );
        CREATE INDEX ix_ref_cctv_growth_gu_name ON ref_cctv_growth (gu_name);

        CREATE TABLE ref_safepath (
            id SERIAL PRIMARY KEY,
            region_code VARCHAR,
            length_m DOUBLE PRECISION,
            raw_score DOUBLE PRECISION
        );
        CREATE INDEX ix_ref_safepath_region_code ON ref_safepath (region_code);

        CREATE TABLE ref_flood_trace (
            id SERIAL PRIMARY KEY,
            geom geometry(MULTIPOLYGON, 4326) NOT NULL,
            properties JSONB
        );
        CREATE INDEX idx_ref_flood_trace_geom ON ref_flood_trace USING GIST (geom);

        CREATE TABLE ref_flood_pump (
            id SERIAL PRIMARY KEY,
            name VARCHAR,
            address VARCHAR,
            max_capacity DOUBLE PRECISION,
            lat DOUBLE PRECISION NOT NULL,
            lon DOUBLE PRECISION NOT NULL,
            geom geometry(POINT, 4326) NOT NULL,
            raw_score DOUBLE PRECISION
        );
        CREATE INDEX idx_ref_flood_pump_geom ON ref_flood_pump USING GIST (geom);

        CREATE TABLE ref_impervious (
            id SERIAL PRIMARY KEY,
            gu_name VARCHAR NOT NULL UNIQUE,
            impervious_ratio DOUBLE PRECISION,
            raw_score DOUBLE PRECISION
        );
        CREATE INDEX ix_ref_impervious_gu_name ON ref_impervious (gu_name);

        CREATE TABLE ref_noise_pub (
            id SERIAL PRIMARY KEY,
            name VARCHAR,
            address VARCHAR,
            lat DOUBLE PRECISION NOT NULL,
            lon DOUBLE PRECISION NOT NULL,
            geom geometry(POINT, 4326) NOT NULL,
            raw_score DOUBLE PRECISION
        );
        CREATE INDEX idx_ref_noise_pub_geom ON ref_noise_pub USING GIST (geom);

        CREATE TABLE ref_noise_road (
            id SERIAL PRIMARY KEY,
            its_link_id VARCHAR,
            road_name VARCHAR,
            region VARCHAR,
            raw_score DOUBLE PRECISION
        );
        CREATE INDEX ix_ref_noise_road_its_link_id ON ref_noise_road (its_link_id);
        CREATE INDEX ix_ref_noise_road_region ON ref_noise_road (region);

        CREATE TABLE ref_noise_rail (
            id SERIAL PRIMARY KEY,
            from_station VARCHAR,
            from_line VARCHAR,
            to_station VARCHAR,
            to_line VARCHAR,
            distance DOUBLE PRECISION,
            raw_score DOUBLE PRECISION
        );

        CREATE TABLE ref_noise_complaint (
            id SERIAL PRIMARY KEY,
            gu_name VARCHAR NOT NULL UNIQUE,
            raw_score DOUBLE PRECISION
        );
        CREATE INDEX ix_ref_noise_complaint_gu_name ON ref_noise_complaint (gu_name);

        CREATE TABLE ref_noise_measurement (
            id SERIAL PRIMARY KEY,
            station VARCHAR,
            address VARCHAR,
            land_use VARCHAR,
            leq DOUBLE PRECISION,
            raw_score DOUBLE PRECISION
        );
        CREATE INDEX ix_ref_noise_measurement_station ON ref_noise_measurement (station);

        CREATE TABLE ref_noise_aircraft (
            id SERIAL PRIMARY KEY,
            station VARCHAR,
            raw_score DOUBLE PRECISION
        );
        CREATE INDEX ix_ref_noise_aircraft_station ON ref_noise_aircraft (station);

        CREATE TABLE ref_noise_hourly (
            id SERIAL PRIMARY KEY,
            station VARCHAR,
            hour VARCHAR,
            raw_score DOUBLE PRECISION
        );
        CREATE INDEX ix_ref_noise_hourly_station ON ref_noise_hourly (station);

        CREATE TABLE ref_night_clinic (
            id SERIAL PRIMARY KEY,
            name VARCHAR,
            gu_name VARCHAR,
            dong_name VARCHAR,
            lat DOUBLE PRECISION NOT NULL,
            lon DOUBLE PRECISION NOT NULL,
            geom geometry(POINT, 4326) NOT NULL,
            raw_score DOUBLE PRECISION
        );
        CREATE INDEX ix_ref_night_clinic_gu_name ON ref_night_clinic (gu_name);
        CREATE INDEX ix_ref_night_clinic_dong_name ON ref_night_clinic (dong_name);
        CREATE INDEX idx_ref_night_clinic_geom ON ref_night_clinic USING GIST (geom);

        CREATE TABLE ref_pharmacy (
            id SERIAL PRIMARY KEY,
            name VARCHAR,
            gu_name VARCHAR,
            dong_name VARCHAR,
            lat DOUBLE PRECISION NOT NULL,
            lon DOUBLE PRECISION NOT NULL,
            geom geometry(POINT, 4326) NOT NULL,
            raw_score DOUBLE PRECISION
        );
        CREATE INDEX ix_ref_pharmacy_gu_name ON ref_pharmacy (gu_name);
        CREATE INDEX ix_ref_pharmacy_dong_name ON ref_pharmacy (dong_name);
        CREATE INDEX idx_ref_pharmacy_geom ON ref_pharmacy USING GIST (geom);

        CREATE TABLE ref_health_dong (
            id SERIAL PRIMARY KEY,
            gu_name VARCHAR,
            dong_name VARCHAR,
            night_clinic_count DOUBLE PRECISION,
            raw_score_clinic DOUBLE PRECISION,
            pharmacy_count DOUBLE PRECISION,
            raw_score_pharmacy DOUBLE PRECISION
        );
        CREATE INDEX ix_ref_health_dong_gu_name ON ref_health_dong (gu_name);
        CREATE INDEX ix_ref_health_dong_dong_name ON ref_health_dong (dong_name);

        CREATE TABLE ref_health_workforce (
            id SERIAL PRIMARY KEY,
            gu_name VARCHAR NOT NULL UNIQUE,
            nurse_count INTEGER,
            specialist_count INTEGER,
            raw_score DOUBLE PRECISION
        );
        CREATE INDEX ix_ref_health_workforce_gu_name ON ref_health_workforce (gu_name);

        CREATE TABLE ref_bus_stop (
            id SERIAL PRIMARY KEY,
            node_id VARCHAR,
            ars_id VARCHAR,
            stop_name VARCHAR,
            stop_type VARCHAR,
            lat DOUBLE PRECISION NOT NULL,
            lon DOUBLE PRECISION NOT NULL,
            geom geometry(POINT, 4326) NOT NULL,
            daily_avg_usage DOUBLE PRECISION,
            raw_score DOUBLE PRECISION
        );
        CREATE INDEX ix_ref_bus_stop_node_id ON ref_bus_stop (node_id);
        CREATE INDEX idx_ref_bus_stop_geom ON ref_bus_stop USING GIST (geom);

        CREATE TABLE ref_bus_hourly (
            id SERIAL PRIMARY KEY,
            node_id VARCHAR,
            stop_name VARCHAR,
            lat DOUBLE PRECISION NOT NULL,
            lon DOUBLE PRECISION NOT NULL,
            geom geometry(POINT, 4326) NOT NULL,
            hourly_pop JSONB
        );
        CREATE INDEX ix_ref_bus_hourly_node_id ON ref_bus_hourly (node_id);
        CREATE INDEX idx_ref_bus_hourly_geom ON ref_bus_hourly USING GIST (geom);

        CREATE TABLE ref_subway_congestion (
            id SERIAL PRIMARY KEY,
            station_name VARCHAR NOT NULL UNIQUE,
            peak_max_congestion DOUBLE PRECISION,
            raw_score DOUBLE PRECISION
        );
        CREATE INDEX ix_ref_subway_congestion_station_name ON ref_subway_congestion (station_name);

        CREATE TABLE ref_floating_pop (
            id SERIAL PRIMARY KEY,
            dong_code VARCHAR NOT NULL UNIQUE,
            total_pop DOUBLE PRECISION,
            raw_score DOUBLE PRECISION
        );
        CREATE INDEX ix_ref_floating_pop_dong_code ON ref_floating_pop (dong_code);
        """.split(";"):
        if statement.strip():
            op.execute(statement)


def downgrade() -> None:
    for table_name in (
        "ref_floating_pop",
        "ref_subway_congestion",
        "ref_bus_hourly",
        "ref_bus_stop",
        "ref_health_workforce",
        "ref_health_dong",
        "ref_pharmacy",
        "ref_night_clinic",
        "ref_noise_hourly",
        "ref_noise_aircraft",
        "ref_noise_measurement",
        "ref_noise_complaint",
        "ref_noise_rail",
        "ref_noise_road",
        "ref_noise_pub",
        "ref_impervious",
        "ref_flood_pump",
        "ref_flood_trace",
        "ref_safepath",
        "ref_cctv_growth",
        "ref_police_pop",
        "ref_crime",
        "ref_police",
        "ref_light_blind",
        "ref_cctv",
    ):
        op.execute(f"DROP TABLE IF EXISTS {table_name};")
    op.execute("DROP EXTENSION IF EXISTS postgis CASCADE;")
