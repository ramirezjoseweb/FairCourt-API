"""add daily reservation limit

Revision ID: 0a1b2c3d4e5f
Revises: f1a2b3c4d5e6
Create Date: 2026-09-20
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0a1b2c3d4e5f"
down_revision: Union[str, Sequence[str], None] = "f1a2b3c4d5e6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("community_policies") as batch_op:
        batch_op.add_column(
            sa.Column(
                "max_active_reservations_per_day",
                sa.Integer(),
                nullable=False,
                server_default=sa.text("1"),
            )
        )
        batch_op.create_check_constraint(
            "ck_policy_daily_reservation_limit",
            "max_active_reservations_per_day >= 0",
        )


def downgrade() -> None:
    with op.batch_alter_table("community_policies") as batch_op:
        batch_op.drop_constraint(
            "ck_policy_daily_reservation_limit",
            type_="check",
        )
        batch_op.drop_column("max_active_reservations_per_day")
