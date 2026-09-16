"""add community tenant scope

Revision ID: c8d4e5f6a7b8
Revises: b7c3f8a2d941
Create Date: 2026-09-15
"""

from datetime import datetime
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c8d4e5f6a7b8"
down_revision: Union[str, Sequence[str], None] = "b7c3f8a2d941"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


SCOPED_TABLES = (
    "auth_otps",
    "households",
    "users",
    "facilities",
    "reservations",
    "waitlist_entries",
    "audit_log",
    "unlock_proposals",
    "unlock_votes",
    "notifications",
)


def upgrade() -> None:
    op.create_table(
        "communities",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("slug", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("timezone", sa.String(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_communities_id", "communities", ["id"], unique=False)
    op.create_index("ix_communities_slug", "communities", ["slug"], unique=True)
    op.bulk_insert(
        sa.table(
            "communities",
            sa.column("id", sa.Integer),
            sa.column("slug", sa.String),
            sa.column("name", sa.String),
            sa.column("timezone", sa.String),
            sa.column("is_active", sa.Boolean),
            sa.column("created_at", sa.DateTime),
        ),
        [
            {
                "id": 1,
                "slug": "faircourt",
                "name": "Comunidad FairCourt",
                "timezone": "Europe/Madrid",
                "is_active": True,
                "created_at": datetime.utcnow(),
            }
        ],
    )

    for table_name in SCOPED_TABLES:
        op.add_column(
            table_name,
            sa.Column("community_id", sa.Integer(), nullable=True),
        )
        op.execute(sa.text(f"UPDATE {table_name} SET community_id = 1"))

    op.add_column(
        "households",
        sa.Column("code_normalized", sa.String(), nullable=True),
    )
    op.execute(
        sa.text("UPDATE households SET code_normalized = UPPER(TRIM(code))")
    )

    with op.batch_alter_table("households") as batch_op:
        batch_op.drop_index("ix_households_code")
        batch_op.alter_column(
            "community_id", existing_type=sa.Integer(), nullable=False
        )
        batch_op.alter_column(
            "code_normalized", existing_type=sa.String(), nullable=False
        )
        batch_op.create_foreign_key(
            "fk_households_community_id",
            "communities",
            ["community_id"],
            ["id"],
        )
        batch_op.create_unique_constraint(
            "uq_households_community_code",
            ["community_id", "code_normalized"],
        )
        batch_op.create_index(
            "ix_households_community_code",
            ["community_id", "code_normalized"],
            unique=False,
        )

    with op.batch_alter_table("facilities") as batch_op:
        batch_op.drop_index("ix_facilities_slug")
        batch_op.alter_column(
            "community_id", existing_type=sa.Integer(), nullable=False
        )
        batch_op.create_foreign_key(
            "fk_facilities_community_id",
            "communities",
            ["community_id"],
            ["id"],
        )
        batch_op.create_unique_constraint(
            "uq_facilities_community_slug",
            ["community_id", "slug"],
        )
        batch_op.create_index(
            "ix_facilities_community_priority",
            ["community_id", "priority"],
            unique=False,
        )

    simple_scopes = (
        ("auth_otps", "fk_auth_otps_community_id", None),
        ("users", "fk_users_community_id", None),
        (
            "reservations",
            "fk_reservations_community_id",
            ("ix_reservations_community_start", ["community_id", "start_at"]),
        ),
        (
            "waitlist_entries",
            "fk_waitlist_entries_community_id",
            ("ix_waitlist_community_start", ["community_id", "start_at"]),
        ),
        (
            "audit_log",
            "fk_audit_log_community_id",
            ("ix_audit_log_community_id", ["community_id"]),
        ),
        (
            "unlock_proposals",
            "fk_unlock_proposals_community_id",
            ("ix_unlock_proposals_community_id", ["community_id"]),
        ),
        (
            "unlock_votes",
            "fk_unlock_votes_community_id",
            ("ix_unlock_votes_community_id", ["community_id"]),
        ),
        (
            "notifications",
            "fk_notifications_community_id",
            ("ix_notifications_community_id", ["community_id"]),
        ),
    )
    for table_name, foreign_key_name, index in simple_scopes:
        with op.batch_alter_table(table_name) as batch_op:
            batch_op.alter_column(
                "community_id", existing_type=sa.Integer(), nullable=False
            )
            batch_op.create_foreign_key(
                foreign_key_name,
                "communities",
                ["community_id"],
                ["id"],
            )
            if index:
                batch_op.create_index(index[0], index[1], unique=False)


def downgrade() -> None:
    connection = op.get_bind()
    duplicate_household = connection.execute(
        sa.text(
            "SELECT code_normalized FROM households "
            "GROUP BY code_normalized HAVING COUNT(*) > 1 LIMIT 1"
        )
    ).first()
    duplicate_facility = connection.execute(
        sa.text(
            "SELECT slug FROM facilities "
            "GROUP BY slug HAVING COUNT(*) > 1 LIMIT 1"
        )
    ).first()
    if duplicate_household or duplicate_facility:
        raise RuntimeError(
            "No se puede revertir el ámbito multi-comunidad mientras existan "
            "códigos de vivienda o slugs de instalación repetidos entre comunidades."
        )

    simple_scopes = (
        (
            "notifications",
            "fk_notifications_community_id",
            "ix_notifications_community_id",
        ),
        (
            "unlock_votes",
            "fk_unlock_votes_community_id",
            "ix_unlock_votes_community_id",
        ),
        (
            "unlock_proposals",
            "fk_unlock_proposals_community_id",
            "ix_unlock_proposals_community_id",
        ),
        ("audit_log", "fk_audit_log_community_id", "ix_audit_log_community_id"),
        (
            "waitlist_entries",
            "fk_waitlist_entries_community_id",
            "ix_waitlist_community_start",
        ),
        (
            "reservations",
            "fk_reservations_community_id",
            "ix_reservations_community_start",
        ),
        ("users", "fk_users_community_id", None),
        ("auth_otps", "fk_auth_otps_community_id", None),
    )
    for table_name, foreign_key_name, index_name in simple_scopes:
        with op.batch_alter_table(table_name) as batch_op:
            if index_name:
                batch_op.drop_index(index_name)
            batch_op.drop_constraint(foreign_key_name, type_="foreignkey")
            batch_op.drop_column("community_id")

    with op.batch_alter_table("facilities") as batch_op:
        batch_op.drop_index("ix_facilities_community_priority")
        batch_op.drop_constraint(
            "uq_facilities_community_slug", type_="unique"
        )
        batch_op.drop_constraint(
            "fk_facilities_community_id", type_="foreignkey"
        )
        batch_op.drop_column("community_id")
        batch_op.create_index("ix_facilities_slug", ["slug"], unique=True)

    with op.batch_alter_table("households") as batch_op:
        batch_op.drop_index("ix_households_community_code")
        batch_op.drop_constraint(
            "uq_households_community_code", type_="unique"
        )
        batch_op.drop_constraint(
            "fk_households_community_id", type_="foreignkey"
        )
        batch_op.drop_column("code_normalized")
        batch_op.drop_column("community_id")
        batch_op.create_index("ix_households_code", ["code"], unique=True)

    op.drop_index("ix_communities_slug", table_name="communities")
    op.drop_index("ix_communities_id", table_name="communities")
    op.drop_table("communities")
