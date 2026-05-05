"""remove unique constraint on reservation start_at

Revision ID: d423a36c2075
Revises: ee23857a8e9a
Create Date: 2026-03-20 04:02:23.248409

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd423a36c2075'
down_revision: Union[str, Sequence[str], None] = 'ee23857a8e9a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# borra la restriccion de UNIQUE en start_at con batch_alter_table
def upgrade() -> None:
    with op.batch_alter_table("reservations") as batch_op:
        batch_op.drop_constraint("uq_reservations_start_at", type_="unique")

# rehace la restriccion UNIQUE en start_at con batch_alter_table
def downgrade() -> None:
    with op.batch_alter_table("reservations") as batch_op:
        batch_op.create_unique_constraint("uq_reservations_start_at", ["start_at"])
