"""add noise detail reference columns

Revision ID: a5b6c7d8e9f0
Revises: f4a5b6c7d8e9
Create Date: 2026-05-15 00:00:00.000000
"""

from alembic import op


revision = "a5b6c7d8e9f0"
down_revision = "f4a5b6c7d8e9"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TABLE ref_noise_measurement ADD COLUMN IF NOT EXISTS lat DOUBLE PRECISION")
    op.execute("ALTER TABLE ref_noise_measurement ADD COLUMN IF NOT EXISTS lon DOUBLE PRECISION")
    op.execute("ALTER TABLE ref_noise_measurement ADD COLUMN IF NOT EXISTS radius_m DOUBLE PRECISION")
    op.execute("ALTER TABLE ref_noise_measurement ADD COLUMN IF NOT EXISTS geom geometry(POINT, 4326)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_ref_noise_measurement_geom ON ref_noise_measurement USING gist (geom)")

    op.execute("ALTER TABLE ref_noise_hourly ADD COLUMN IF NOT EXISTS time_penalty DOUBLE PRECISION")
    op.execute("ALTER TABLE ref_noise_hourly ADD COLUMN IF NOT EXISTS lden_score DOUBLE PRECISION")


def downgrade() -> None:
    op.execute("ALTER TABLE ref_noise_hourly DROP COLUMN IF EXISTS lden_score")
    op.execute("ALTER TABLE ref_noise_hourly DROP COLUMN IF EXISTS time_penalty")

    op.execute("DROP INDEX IF EXISTS idx_ref_noise_measurement_geom")
    op.execute("ALTER TABLE ref_noise_measurement DROP COLUMN IF EXISTS geom")
    op.execute("ALTER TABLE ref_noise_measurement DROP COLUMN IF EXISTS radius_m")
    op.execute("ALTER TABLE ref_noise_measurement DROP COLUMN IF EXISTS lon")
    op.execute("ALTER TABLE ref_noise_measurement DROP COLUMN IF EXISTS lat")
