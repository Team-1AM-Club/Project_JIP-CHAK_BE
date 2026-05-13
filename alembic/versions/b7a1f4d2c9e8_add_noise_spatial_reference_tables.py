"""add noise spatial reference tables

Revision ID: b7a1f4d2c9e8
Revises: 65588f32ed90
Create Date: 2026-05-13 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import geoalchemy2
import sqlalchemy as sa


revision: str = "b7a1f4d2c9e8"
down_revision: Union[str, Sequence[str], None] = "65588f32ed90"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "ref_noise_idw_grid",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("grid_lat", sa.Float(), nullable=False),
        sa.Column("grid_lon", sa.Float(), nullable=False),
        sa.Column("estimated_db", sa.Float(), nullable=False),
        sa.Column(
            "geom",
            geoalchemy2.types.Geometry(geometry_type="POINT", srid=4326, spatial_index=False),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_ref_noise_idw_grid_geom",
        "ref_noise_idw_grid",
        ["geom"],
        unique=False,
        postgresql_using="gist",
    )

    op.create_table(
        "ref_noise_lden_point",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("station", sa.String(), nullable=True),
        sa.Column("lat", sa.Float(), nullable=False),
        sa.Column("lon", sa.Float(), nullable=False),
        sa.Column("radius_m", sa.Float(), nullable=True),
        sa.Column("raw_score", sa.Float(), nullable=True),
        sa.Column(
            "geom",
            geoalchemy2.types.Geometry(geometry_type="POINT", srid=4326, spatial_index=False),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_ref_noise_lden_point_station", "ref_noise_lden_point", ["station"], unique=False)
    op.create_index(
        "idx_ref_noise_lden_point_geom",
        "ref_noise_lden_point",
        ["geom"],
        unique=False,
        postgresql_using="gist",
    )

    op.create_table(
        "ref_noise_traffic_point",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("point_no", sa.String(), nullable=True),
        sa.Column("point_name", sa.String(), nullable=True),
        sa.Column("daily_traffic", sa.Float(), nullable=True),
        sa.Column("night_traffic", sa.Float(), nullable=True),
        sa.Column("lat", sa.Float(), nullable=False),
        sa.Column("lon", sa.Float(), nullable=False),
        sa.Column("raw_score", sa.Float(), nullable=True),
        sa.Column(
            "geom",
            geoalchemy2.types.Geometry(geometry_type="POINT", srid=4326, spatial_index=False),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_ref_noise_traffic_point_point_no", "ref_noise_traffic_point", ["point_no"], unique=False)
    op.create_index(
        "idx_ref_noise_traffic_point_geom",
        "ref_noise_traffic_point",
        ["geom"],
        unique=False,
        postgresql_using="gist",
    )


def downgrade() -> None:
    op.drop_index("idx_ref_noise_traffic_point_geom", table_name="ref_noise_traffic_point", postgresql_using="gist")
    op.drop_index("ix_ref_noise_traffic_point_point_no", table_name="ref_noise_traffic_point")
    op.drop_table("ref_noise_traffic_point")
    op.drop_index("idx_ref_noise_lden_point_geom", table_name="ref_noise_lden_point", postgresql_using="gist")
    op.drop_index("ix_ref_noise_lden_point_station", table_name="ref_noise_lden_point")
    op.drop_table("ref_noise_lden_point")
    op.drop_index("idx_ref_noise_idw_grid_geom", table_name="ref_noise_idw_grid", postgresql_using="gist")
    op.drop_table("ref_noise_idw_grid")
