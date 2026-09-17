"""add platform admin roles and private audit scope

Revision ID: e0f1a2b3c4d5
Revises: d9e0f1a2b3c4
Create Date: 2026-09-17
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "e0f1a2b3c4d5"
down_revision: Union[str, Sequence[str], None] = "d9e0f1a2b3c4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("users") as batch_op:
        batch_op.add_column(
            sa.Column(
                "role",
                sa.String(),
                server_default="resident",
                nullable=False,
            )
        )
        batch_op.add_column(
            sa.Column(
                "is_active",
                sa.Boolean(),
                server_default=sa.true(),
                nullable=False,
            )
        )
        batch_op.alter_column(
            "community_id",
            existing_type=sa.Integer(),
            nullable=True,
        )
        batch_op.alter_column(
            "household_id",
            existing_type=sa.Integer(),
            nullable=True,
        )
        batch_op.create_check_constraint(
            "ck_users_role_scope",
            "(role = 'resident' AND community_id IS NOT NULL "
            "AND household_id IS NOT NULL) OR "
            "(role = 'platform_admin' AND community_id IS NULL "
            "AND household_id IS NULL)",
        )
        batch_op.create_index("ix_users_role", ["role"], unique=False)

    with op.batch_alter_table("auth_otps") as batch_op:
        batch_op.add_column(
            sa.Column(
                "purpose",
                sa.String(),
                server_default="RESIDENT",
                nullable=False,
            )
        )
        batch_op.alter_column(
            "community_id",
            existing_type=sa.Integer(),
            nullable=True,
        )
        batch_op.create_index("ix_auth_otps_purpose", ["purpose"], unique=False)

    with op.batch_alter_table("audit_log") as batch_op:
        batch_op.add_column(
            sa.Column(
                "visibility",
                sa.String(),
                server_default="resident",
                nullable=False,
            )
        )
        batch_op.alter_column(
            "community_id",
            existing_type=sa.Integer(),
            nullable=True,
        )
        batch_op.create_check_constraint(
            "ck_audit_log_visibility",
            "visibility IN ('resident', 'admin')",
        )
        batch_op.create_index(
            "ix_audit_log_visibility",
            ["visibility"],
            unique=False,
        )


def downgrade() -> None:
    op.execute("DELETE FROM audit_log WHERE visibility = 'admin'")
    op.execute("DELETE FROM auth_otps WHERE purpose = 'PLATFORM_ADMIN'")
    op.execute("DELETE FROM users WHERE role = 'platform_admin'")

    with op.batch_alter_table("audit_log") as batch_op:
        batch_op.drop_index("ix_audit_log_visibility")
        batch_op.drop_constraint("ck_audit_log_visibility", type_="check")
        batch_op.alter_column(
            "community_id",
            existing_type=sa.Integer(),
            nullable=False,
        )
        batch_op.drop_column("visibility")

    with op.batch_alter_table("auth_otps") as batch_op:
        batch_op.drop_index("ix_auth_otps_purpose")
        batch_op.alter_column(
            "community_id",
            existing_type=sa.Integer(),
            nullable=False,
        )
        batch_op.drop_column("purpose")

    with op.batch_alter_table("users") as batch_op:
        batch_op.drop_index("ix_users_role")
        batch_op.drop_constraint("ck_users_role_scope", type_="check")
        batch_op.alter_column(
            "household_id",
            existing_type=sa.Integer(),
            nullable=False,
        )
        batch_op.alter_column(
            "community_id",
            existing_type=sa.Integer(),
            nullable=False,
        )
        batch_op.drop_column("is_active")
        batch_op.drop_column("role")
