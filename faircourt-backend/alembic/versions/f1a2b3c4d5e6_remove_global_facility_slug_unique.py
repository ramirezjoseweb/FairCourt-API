"""remove obsolete global facility slug uniqueness

Revision ID: f1a2b3c4d5e6
Revises: e0f1a2b3c4d5
Create Date: 2026-09-17
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "f1a2b3c4d5e6"
down_revision: Union[str, Sequence[str], None] = "e0f1a2b3c4d5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _facilities_table() -> sa.Table:
    metadata = sa.MetaData()
    return sa.Table(
        "facilities",
        metadata,
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("slug", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("category", sa.String(), nullable=False),
        sa.Column("description", sa.String(), nullable=True),
        sa.Column("icon", sa.String(), nullable=False),
        sa.Column("priority", sa.Integer(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("is_reservable", sa.Boolean(), nullable=False),
        sa.Column("opening_hour", sa.Integer(), nullable=False),
        sa.Column("closing_hour", sa.Integer(), nullable=False),
        sa.Column("slot_duration_minutes", sa.Integer(), nullable=False),
        sa.Column("community_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["community_id"],
            ["communities.id"],
            name="fk_facilities_community_id",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "community_id",
            "slug",
            name="uq_facilities_community_slug",
        ),
        sa.Index("ix_facilities_id", "id"),
        sa.Index(
            "ix_facilities_community_priority",
            "community_id",
            "priority",
        ),
    )


def upgrade() -> None:
    # La tabla original declaraba slug unique=True. La migración multi-comunidad
    # añadió la unicidad compuesta, pero SQLite conservó también UNIQUE(slug).
    # copy_from fuerza una reconstrucción exacta sin esa restricción anónima.
    with op.batch_alter_table(
        "facilities",
        recreate="always",
        copy_from=_facilities_table(),
    ):
        pass


def downgrade() -> None:
    with op.batch_alter_table("facilities") as batch_op:
        batch_op.create_unique_constraint(
            "uq_facilities_slug_global",
            ["slug"],
        )
