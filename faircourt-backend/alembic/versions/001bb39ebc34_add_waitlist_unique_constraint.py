"""add waitlist unique constraint

Revision ID: 001bb39ebc34
Revises: d423a36c2075
Create Date: 2026-03-20 14:08:23.551037

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '001bb39ebc34'
down_revision: Union[str, Sequence[str], None] = 'd423a36c2075'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    with op.batch_alter_table("reservations") as batch_op:
        batch_op.create_unique_constraint(
            "uq_waitlist_household_start",
            ["household_id", "start_at"]
        )


def downgrade():
    with op.batch_alter_table("reservations") as batch_op:
        batch_op.drop_constraint(
            "uq_waitlist_household_start",
            type_="unique"
        )
