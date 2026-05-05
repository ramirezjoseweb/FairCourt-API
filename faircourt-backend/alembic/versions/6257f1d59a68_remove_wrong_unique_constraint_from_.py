"""remove wrong unique constraint from reservation

Revision ID: 6257f1d59a68
Revises: 001bb39ebc34
Create Date: 2026-03-25 20:20:10.782604

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "6257f1d59a68"
down_revision = "001bb39ebc34"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("reservations") as batch_op:
        batch_op.drop_constraint("uq_waitlist_household_start", type_="unique")


def downgrade() -> None:
    with op.batch_alter_table("reservations") as batch_op:
        batch_op.create_unique_constraint(
            "uq_waitlist_household_start",
            ["household_id", "start_at"]
        )
