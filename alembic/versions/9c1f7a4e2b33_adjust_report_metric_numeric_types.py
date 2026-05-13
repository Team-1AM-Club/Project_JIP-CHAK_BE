"""adjust report metric numeric types

Revision ID: 9c1f7a4e2b33
Revises: 7b3f4c2d1a90
Create Date: 2026-05-12 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "9c1f7a4e2b33"
down_revision: Union[str, Sequence[str], None] = "7b3f4c2d1a90"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        "reports",
        "low_ratio",
        existing_type=sa.SmallInteger(),
        type_=sa.Float(),
        existing_nullable=False,
        postgresql_using="low_ratio::double precision",
    )
    op.alter_column(
        "reports",
        "pump_cap",
        existing_type=sa.SmallInteger(),
        type_=sa.Float(),
        existing_nullable=False,
        postgresql_using="pump_cap::double precision",
    )
    op.alter_column(
        "reports",
        "road_noise",
        existing_type=sa.SmallInteger(),
        type_=sa.Float(),
        existing_nullable=False,
        postgresql_using="road_noise::double precision",
    )


def downgrade() -> None:
    op.alter_column(
        "reports",
        "road_noise",
        existing_type=sa.Float(),
        type_=sa.SmallInteger(),
        existing_nullable=False,
        postgresql_using="round(road_noise)::smallint",
    )
    op.alter_column(
        "reports",
        "pump_cap",
        existing_type=sa.Float(),
        type_=sa.SmallInteger(),
        existing_nullable=False,
        postgresql_using="round(pump_cap)::smallint",
    )
    op.alter_column(
        "reports",
        "low_ratio",
        existing_type=sa.Float(),
        type_=sa.SmallInteger(),
        existing_nullable=False,
        postgresql_using="round(low_ratio)::smallint",
    )
