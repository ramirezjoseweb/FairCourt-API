"""add facilities and associate bookings with them

Revision ID: b7c3f8a2d941
Revises: 933062b76648
Create Date: 2026-09-10
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b7c3f8a2d941"
down_revision: Union[str, Sequence[str], None] = "933062b76648"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


FACILITIES = [
    (1, "padel", "Pádel", "Deporte", "La instalación más solicitada", "court", 10, 9, 22, 60),
    (2, "tenis", "Tenis", "Deporte", "Pista de tenis comunitaria", "court", 20, 9, 22, 60),
    (3, "pergola-1", "Pérgola 1", "Encuentros", "Espacio cubierto para reuniones", "calendar", 30, 9, 23, 60),
    (4, "pergola-2", "Pérgola 2", "Encuentros", "Espacio cubierto para reuniones", "calendar", 31, 9, 23, 60),
    (5, "pergola-3", "Pérgola 3", "Encuentros", "Espacio cubierto para reuniones", "calendar", 32, 9, 23, 60),
    (6, "pergola-4", "Pérgola 4", "Encuentros", "Espacio cubierto para reuniones", "calendar", 33, 9, 23, 60),
    (7, "petanca", "Petanca", "Deporte", "Pista de petanca", "court", 40, 9, 22, 60),
    (8, "polideportiva", "Fútbol / baloncesto / polideportiva", "Deporte", "Pista polideportiva", "court", 41, 9, 22, 60),
    (9, "barra-bar", "Barra de bar", "Encuentros", "Zona de barra comunitaria", "calendar", 50, 9, 23, 60),
    (10, "mesa-1", "Mesa 1", "Mesas", "Mesa reservable", "calendar", 60, 9, 23, 60),
    (11, "mesa-2", "Mesa 2", "Mesas", "Mesa reservable", "calendar", 61, 9, 23, 60),
    (12, "mesa-3", "Mesa 3", "Mesas", "Mesa reservable", "calendar", 62, 9, 23, 60),
    (13, "mesa-4", "Mesa 4", "Mesas", "Mesa reservable", "calendar", 63, 9, 23, 60),
    (14, "sala-multiusos", "Sala multiusos · Tenis de mesa", "Interior", "Sala comunitaria polivalente", "home", 70, 9, 22, 60),
    (15, "sauna", "Sauna", "Bienestar", "Sauna comunitaria", "shield", 80, 9, 22, 60),
]


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    waitlist_unique_names = {
        item["name"] for item in inspector.get_unique_constraints("waitlist_entries")
    }
    waitlist_index_names = {
        item["name"] for item in inspector.get_indexes("waitlist_entries")
    }

    op.create_table(
        "facilities",
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
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slug"),
    )
    op.create_index(op.f("ix_facilities_id"), "facilities", ["id"], unique=False)
    op.create_index(op.f("ix_facilities_slug"), "facilities", ["slug"], unique=True)

    facilities = sa.table(
        "facilities",
        sa.column("id", sa.Integer),
        sa.column("slug", sa.String),
        sa.column("name", sa.String),
        sa.column("category", sa.String),
        sa.column("description", sa.String),
        sa.column("icon", sa.String),
        sa.column("priority", sa.Integer),
        sa.column("is_active", sa.Boolean),
        sa.column("is_reservable", sa.Boolean),
        sa.column("opening_hour", sa.Integer),
        sa.column("closing_hour", sa.Integer),
        sa.column("slot_duration_minutes", sa.Integer),
    )
    op.bulk_insert(
        facilities,
        [
            {
                "id": row[0], "slug": row[1], "name": row[2], "category": row[3],
                "description": row[4], "icon": row[5], "priority": row[6],
                "is_active": True, "is_reservable": True,
                "opening_hour": row[7], "closing_hour": row[8],
                "slot_duration_minutes": row[9],
            }
            for row in FACILITIES
        ],
    )

    op.add_column("reservations", sa.Column("facility_id", sa.Integer(), nullable=True))
    op.add_column("waitlist_entries", sa.Column("facility_id", sa.Integer(), nullable=True))
    op.execute("UPDATE reservations SET facility_id = 1")
    op.execute("UPDATE waitlist_entries SET facility_id = 1")

    with op.batch_alter_table("reservations") as batch_op:
        batch_op.alter_column("facility_id", existing_type=sa.Integer(), nullable=False)
        batch_op.create_foreign_key("fk_reservations_facility_id", "facilities", ["facility_id"], ["id"])
        batch_op.create_index("ix_reservations_facility_start", ["facility_id", "start_at"], unique=False)

    with op.batch_alter_table("waitlist_entries") as batch_op:
        if "ix_waitlist_start_created" in waitlist_index_names:
            batch_op.drop_index("ix_waitlist_start_created")
        if "uq_waitlist_household_start" in waitlist_unique_names:
            batch_op.drop_constraint("uq_waitlist_household_start", type_="unique")
        batch_op.alter_column("facility_id", existing_type=sa.Integer(), nullable=False)
        batch_op.create_foreign_key("fk_waitlist_entries_facility_id", "facilities", ["facility_id"], ["id"])
        batch_op.create_index(
            "ix_waitlist_facility_start_created",
            ["facility_id", "start_at", "created_at"],
            unique=False,
        )
        batch_op.create_unique_constraint(
            "uq_waitlist_household_facility_start",
            ["household_id", "facility_id", "start_at"],
        )


def downgrade() -> None:
    with op.batch_alter_table("waitlist_entries") as batch_op:
        batch_op.drop_constraint("uq_waitlist_household_facility_start", type_="unique")
        batch_op.drop_index("ix_waitlist_facility_start_created")
        batch_op.create_unique_constraint("uq_waitlist_household_start", ["household_id", "start_at"])
        batch_op.create_index("ix_waitlist_start_created", ["start_at", "created_at"], unique=False)
        batch_op.drop_constraint("fk_waitlist_entries_facility_id", type_="foreignkey")
        batch_op.drop_column("facility_id")

    with op.batch_alter_table("reservations") as batch_op:
        batch_op.drop_index("ix_reservations_facility_start")
        batch_op.drop_constraint("fk_reservations_facility_id", type_="foreignkey")
        batch_op.drop_column("facility_id")

    op.drop_index(op.f("ix_facilities_slug"), table_name="facilities")
    op.drop_index(op.f("ix_facilities_id"), table_name="facilities")
    op.drop_table("facilities")
