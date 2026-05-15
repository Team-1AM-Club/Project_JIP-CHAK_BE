"""add congestion detail reference columns

Revision ID: f4a5b6c7d8e9
Revises: e3f4a5b6c7d8
Create Date: 2026-05-15 00:00:00.000000
"""

from alembic import op


revision = "f4a5b6c7d8e9"
down_revision = "e3f4a5b6c7d8"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TABLE ref_subway_congestion DROP CONSTRAINT IF EXISTS ref_subway_congestion_station_name_key")
    op.execute("ALTER TABLE ref_subway_congestion ADD COLUMN IF NOT EXISTS line_name VARCHAR")
    op.execute("ALTER TABLE ref_subway_congestion ADD COLUMN IF NOT EXISTS station_no VARCHAR")
    op.execute("ALTER TABLE ref_subway_congestion ADD COLUMN IF NOT EXISTS lat DOUBLE PRECISION")
    op.execute("ALTER TABLE ref_subway_congestion ADD COLUMN IF NOT EXISTS lon DOUBLE PRECISION")
    op.execute("ALTER TABLE ref_subway_congestion ADD COLUMN IF NOT EXISTS geom geometry(POINT, 4326)")
    op.execute("ALTER TABLE ref_subway_congestion ADD COLUMN IF NOT EXISTS avg_congestion_total DOUBLE PRECISION")
    op.execute("ALTER TABLE ref_subway_congestion ADD COLUMN IF NOT EXISTS avg_congestion_weekday DOUBLE PRECISION")
    op.execute("ALTER TABLE ref_subway_congestion ADD COLUMN IF NOT EXISTS avg_congestion_weekend DOUBLE PRECISION")
    op.execute("ALTER TABLE ref_subway_congestion ADD COLUMN IF NOT EXISTS peak_congestion_total DOUBLE PRECISION")
    op.execute("ALTER TABLE ref_subway_congestion ADD COLUMN IF NOT EXISTS peak_congestion_weekday DOUBLE PRECISION")
    op.execute("ALTER TABLE ref_subway_congestion ADD COLUMN IF NOT EXISTS peak_congestion_weekend DOUBLE PRECISION")
    op.execute("ALTER TABLE ref_subway_congestion ADD COLUMN IF NOT EXISTS daily_passengers_total DOUBLE PRECISION")
    op.execute("ALTER TABLE ref_subway_congestion ADD COLUMN IF NOT EXISTS daily_passengers_weekday DOUBLE PRECISION")
    op.execute("ALTER TABLE ref_subway_congestion ADD COLUMN IF NOT EXISTS daily_passengers_weekend DOUBLE PRECISION")
    op.execute("CREATE INDEX IF NOT EXISTS idx_ref_subway_congestion_geom ON ref_subway_congestion USING gist (geom)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_ref_subway_congestion_line_name ON ref_subway_congestion (line_name)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_ref_subway_congestion_station_no ON ref_subway_congestion (station_no)")

    op.execute("ALTER TABLE ref_floating_pop ADD COLUMN IF NOT EXISTS hourly_pop JSONB")


def downgrade() -> None:
    op.execute("ALTER TABLE ref_floating_pop DROP COLUMN IF EXISTS hourly_pop")
    op.execute("DROP INDEX IF EXISTS ix_ref_subway_congestion_station_no")
    op.execute("DROP INDEX IF EXISTS ix_ref_subway_congestion_line_name")
    op.execute("DROP INDEX IF EXISTS idx_ref_subway_congestion_geom")
    op.execute("ALTER TABLE ref_subway_congestion DROP COLUMN IF EXISTS daily_passengers_weekend")
    op.execute("ALTER TABLE ref_subway_congestion DROP COLUMN IF EXISTS daily_passengers_weekday")
    op.execute("ALTER TABLE ref_subway_congestion DROP COLUMN IF EXISTS daily_passengers_total")
    op.execute("ALTER TABLE ref_subway_congestion DROP COLUMN IF EXISTS peak_congestion_weekend")
    op.execute("ALTER TABLE ref_subway_congestion DROP COLUMN IF EXISTS peak_congestion_weekday")
    op.execute("ALTER TABLE ref_subway_congestion DROP COLUMN IF EXISTS peak_congestion_total")
    op.execute("ALTER TABLE ref_subway_congestion DROP COLUMN IF EXISTS avg_congestion_weekend")
    op.execute("ALTER TABLE ref_subway_congestion DROP COLUMN IF EXISTS avg_congestion_weekday")
    op.execute("ALTER TABLE ref_subway_congestion DROP COLUMN IF EXISTS avg_congestion_total")
    op.execute("ALTER TABLE ref_subway_congestion DROP COLUMN IF EXISTS geom")
    op.execute("ALTER TABLE ref_subway_congestion DROP COLUMN IF EXISTS lon")
    op.execute("ALTER TABLE ref_subway_congestion DROP COLUMN IF EXISTS lat")
    op.execute("ALTER TABLE ref_subway_congestion DROP COLUMN IF EXISTS station_no")
    op.execute("ALTER TABLE ref_subway_congestion DROP COLUMN IF EXISTS line_name")
