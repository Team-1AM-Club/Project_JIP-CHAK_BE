"""add medical detail reference columns

Revision ID: e3f4a5b6c7d8
Revises: d2e3f4a5b6c7
Create Date: 2026-05-14 00:00:00.000000
"""

from alembic import op


revision = "e3f4a5b6c7d8"
down_revision = "d2e3f4a5b6c7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TABLE ref_night_clinic ADD COLUMN IF NOT EXISTS facility_type VARCHAR")
    op.execute("ALTER TABLE ref_night_clinic ADD COLUMN IF NOT EXISTS address VARCHAR")
    op.execute("ALTER TABLE ref_night_clinic ADD COLUMN IF NOT EXISTS close_time INTEGER")
    op.execute("ALTER TABLE ref_pharmacy ADD COLUMN IF NOT EXISTS address VARCHAR")
    op.execute("ALTER TABLE ref_pharmacy ADD COLUMN IF NOT EXISTS close_time INTEGER")


def downgrade() -> None:
    op.execute("ALTER TABLE ref_pharmacy DROP COLUMN IF EXISTS close_time")
    op.execute("ALTER TABLE ref_pharmacy DROP COLUMN IF EXISTS address")
    op.execute("ALTER TABLE ref_night_clinic DROP COLUMN IF EXISTS close_time")
    op.execute("ALTER TABLE ref_night_clinic DROP COLUMN IF EXISTS address")
    op.execute("ALTER TABLE ref_night_clinic DROP COLUMN IF EXISTS facility_type")
