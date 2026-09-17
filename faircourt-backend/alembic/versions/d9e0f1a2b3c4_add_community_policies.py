"""add community policies

Revision ID: d9e0f1a2b3c4
Revises: c8d4e5f6a7b8
Create Date: 2026-09-16
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "d9e0f1a2b3c4"
down_revision: Union[str, Sequence[str], None] = "c8d4e5f6a7b8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "community_policies",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("community_id", sa.Integer(), nullable=False),
        sa.Column("booking_window_days", sa.Integer(), nullable=False),
        sa.Column(
            "max_active_reservations_per_week",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column("cancellation_limit_hours", sa.Integer(), nullable=False),
        sa.Column("checkin_window_minutes", sa.Integer(), nullable=False),
        sa.Column("max_strikes", sa.Integer(), nullable=False),
        sa.Column("suspension_days", sa.Integer(), nullable=False),
        sa.Column(
            "max_active_waitlists_per_week",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column("prime_time_start_hour", sa.Integer(), nullable=False),
        sa.Column("prime_time_end_hour", sa.Integer(), nullable=False),
        sa.Column("cooldown_days", sa.Integer(), nullable=False),
        sa.Column("unlock_voting_enabled", sa.Boolean(), nullable=False),
        sa.Column("unlock_voting_hours", sa.Integer(), nullable=False),
        sa.Column("unlock_min_yes_votes", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint(
            "booking_window_days >= 0",
            name="ck_policy_booking_window",
        ),
        sa.CheckConstraint(
            "max_active_reservations_per_week >= 0",
            name="ck_policy_reservation_limit",
        ),
        sa.CheckConstraint(
            "cancellation_limit_hours >= 0",
            name="ck_policy_cancellation_limit",
        ),
        sa.CheckConstraint(
            "checkin_window_minutes >= 0",
            name="ck_policy_checkin_window",
        ),
        sa.CheckConstraint("max_strikes > 0", name="ck_policy_max_strikes"),
        sa.CheckConstraint(
            "suspension_days >= 0",
            name="ck_policy_suspension_days",
        ),
        sa.CheckConstraint(
            "max_active_waitlists_per_week >= 0",
            name="ck_policy_waitlist_limit",
        ),
        sa.CheckConstraint(
            "prime_time_start_hour >= 0 AND prime_time_start_hour <= 23",
            name="ck_policy_prime_start",
        ),
        sa.CheckConstraint(
            "prime_time_end_hour >= 1 AND prime_time_end_hour <= 24",
            name="ck_policy_prime_end",
        ),
        sa.CheckConstraint(
            "prime_time_start_hour < prime_time_end_hour",
            name="ck_policy_prime_order",
        ),
        sa.CheckConstraint(
            "cooldown_days >= 0",
            name="ck_policy_cooldown_days",
        ),
        sa.CheckConstraint(
            "unlock_voting_hours > 0",
            name="ck_policy_unlock_voting_hours",
        ),
        sa.CheckConstraint(
            "unlock_min_yes_votes > 0",
            name="ck_policy_unlock_min_votes",
        ),
        sa.ForeignKeyConstraint(
            ["community_id"],
            ["communities.id"],
            name="fk_community_policies_community_id",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_community_policies_id",
        "community_policies",
        ["id"],
        unique=False,
    )
    op.create_index(
        "ix_community_policies_community_id",
        "community_policies",
        ["community_id"],
        unique=True,
    )
    op.execute(
        sa.text(
            """
            INSERT INTO community_policies (
                community_id,
                booking_window_days,
                max_active_reservations_per_week,
                cancellation_limit_hours,
                checkin_window_minutes,
                max_strikes,
                suspension_days,
                max_active_waitlists_per_week,
                prime_time_start_hour,
                prime_time_end_hour,
                cooldown_days,
                unlock_voting_enabled,
                unlock_voting_hours,
                unlock_min_yes_votes,
                created_at,
                updated_at
            )
            SELECT
                id, 7, 2, 4, 15, 2, 14, 3, 18, 21, 3, 1, 48, 2,
                CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
            FROM communities
            """
        )
    )


def downgrade() -> None:
    op.drop_index(
        "ix_community_policies_community_id",
        table_name="community_policies",
    )
    op.drop_index(
        "ix_community_policies_id",
        table_name="community_policies",
    )
    op.drop_table("community_policies")
