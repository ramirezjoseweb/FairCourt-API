"""add optional community access prefix

Revision ID: 1b2c3d4e5f60
Revises: 0a1b2c3d4e5f
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "1b2c3d4e5f60"
down_revision: Union[str, Sequence[str], None] = "0a1b2c3d4e5f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("communities") as batch_op:
        batch_op.add_column(sa.Column("access_prefix", sa.String(length=12), nullable=True))
        batch_op.create_unique_constraint(
            "uq_communities_access_prefix", ["access_prefix"]
        )


def downgrade() -> None:
    with op.batch_alter_table("communities") as batch_op:
        batch_op.drop_constraint("uq_communities_access_prefix", type_="unique")
        batch_op.drop_column("access_prefix")
