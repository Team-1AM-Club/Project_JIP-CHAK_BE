"""add flood detail reference tables

Revision ID: d2e3f4a5b6c7
Revises: c4d8e9f1a2b3
Create Date: 2026-05-14 00:00:00.000000
"""

from alembic import op


revision = "d2e3f4a5b6c7"
down_revision = "c4d8e9f1a2b3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS ref_flood_defense (
            id SERIAL PRIMARY KEY,
            gu_name VARCHAR NOT NULL UNIQUE,
            avg_elevation_m DOUBLE PRECISION,
            num_stations DOUBLE PRECISION,
            total_pump_m3 DOUBLE PRECISION,
            total_basin DOUBLE PRECISION,
            pump_efficiency DOUBLE PRECISION,
            max_freq DOUBLE PRECISION,
            avg_coverage_rate DOUBLE PRECISION,
            imperv_proxy DOUBLE PRECISION,
            n_buildings INTEGER,
            score_elevation DOUBLE PRECISION,
            score_pump DOUBLE PRECISION,
            score_imperv DOUBLE PRECISION,
            raw_score DOUBLE PRECISION,
            contour_line_count INTEGER,
            score_contour DOUBLE PRECISION
        )
        """
    )
    op.execute("CREATE INDEX IF NOT EXISTS ix_ref_flood_defense_gu_name ON ref_flood_defense (gu_name)")

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS ref_flood_trace_summary (
            id SERIAL PRIMARY KEY,
            gu_name VARCHAR NOT NULL UNIQUE,
            flood_count DOUBLE PRECISION,
            total_flood_area DOUBLE PRECISION,
            mean_flood_area DOUBLE PRECISION,
            mean_flood_depth DOUBLE PRECISION,
            max_flood_depth DOUBLE PRECISION,
            raw_score DOUBLE PRECISION,
            data_available BOOLEAN,
            data_year INTEGER
        )
        """
    )
    op.execute("CREATE INDEX IF NOT EXISTS ix_ref_flood_trace_summary_gu_name ON ref_flood_trace_summary (gu_name)")

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS ref_flood_trace_point (
            id SERIAL PRIMARY KEY,
            gu_name VARCHAR NOT NULL,
            address VARCHAR,
            flood_year INTEGER,
            flood_area_m2 DOUBLE PRECISION,
            flood_depth_cm DOUBLE PRECISION,
            flood_type VARCHAR,
            lat DOUBLE PRECISION,
            lon DOUBLE PRECISION,
            geom geometry(POINT, 4326),
            is_outlier_area BOOLEAN,
            flood_area_m2_clipped DOUBLE PRECISION,
            raw_score DOUBLE PRECISION
        )
        """
    )
    op.execute("CREATE INDEX IF NOT EXISTS ix_ref_flood_trace_point_gu_name ON ref_flood_trace_point (gu_name)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_ref_flood_trace_point_geom ON ref_flood_trace_point USING gist (geom)")


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS ref_flood_trace_point")
    op.execute("DROP TABLE IF EXISTS ref_flood_trace_summary")
    op.execute("DROP TABLE IF EXISTS ref_flood_defense")
