"""add security detail json

Revision ID: c4d8e9f1a2b3
Revises: b7a1f4d2c9e8
Create Date: 2026-05-14 10:20:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "c4d8e9f1a2b3"
down_revision: Union[str, None] = "b7a1f4d2c9e8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("ref_crime", sa.Column("detail_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.add_column("ref_cctv_growth", sa.Column("detail_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True))


def downgrade() -> None:
    op.drop_column("ref_cctv_growth", "detail_json")
    op.drop_column("ref_crime", "detail_json")
