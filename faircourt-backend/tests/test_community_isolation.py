from __future__ import annotations

import unittest
from datetime import datetime, timedelta

from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.config import settings
from app.db import Base
from app.models import (
    AuditLog,
    AuthOTP,
    Community,
    Facility,
    Household,
    Notification,
    Reservation,
    User,
)
from app.routers.auth import request_otp
from app.routers.facilities import list_facilities
from app.routers.notifications import mark_notification_as_read
from app.routers.reservations import create_reservation
from app.schemas import CreateReservationIn, RequestOTPIn


class CommunityIsolationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(self.engine)
        session_factory = sessionmaker(bind=self.engine)
        self.db: Session = session_factory()

        self.community_a = Community(slug="community-a", name="Comunidad A")
        self.community_b = Community(slug="community-b", name="Comunidad B")
        self.db.add_all([self.community_a, self.community_b])
        self.db.flush()

        self.household_a = Household(
            community_id=self.community_a.id,
            code="Bloque 18 3ºB",
        )
        self.household_b = Household(
            community_id=self.community_b.id,
            code="Bloque 18 3ºB",
        )
        self.facility_a = Facility(
            community_id=self.community_a.id,
            slug="padel",
            name="Pádel A",
            category="Deporte",
        )
        self.facility_b = Facility(
            community_id=self.community_b.id,
            slug="padel",
            name="Pádel B",
            category="Deporte",
        )
        self.db.add_all(
            [
                self.household_a,
                self.household_b,
                self.facility_a,
                self.facility_b,
            ]
        )
        self.db.flush()
        self.user_a = User(
            community_id=self.community_a.id,
            household_id=self.household_a.id,
            email="resident-a@example.com",
        )
        self.user_b = User(
            community_id=self.community_b.id,
            household_id=self.household_b.id,
            email="resident-b@example.com",
        )
        self.db.add_all([self.user_a, self.user_b])
        self.db.commit()

    def tearDown(self) -> None:
        self.db.close()
        self.engine.dispose()

    def test_same_household_code_is_allowed_in_different_communities(self) -> None:
        rows = (
            self.db.query(Household)
            .filter(Household.code_normalized == "BLOQUE 18 3ºB")
            .all()
        )
        self.assertEqual({row.community_id for row in rows}, {1, 2})

    def test_duplicate_household_code_is_rejected_within_community(self) -> None:
        self.db.add(
            Household(
                community_id=self.community_a.id,
                code="  bloque 18 3ºb  ",
            )
        )
        with self.assertRaises(IntegrityError):
            self.db.commit()
        self.db.rollback()

    def test_facility_catalog_is_scoped_to_authenticated_community(self) -> None:
        facilities = list_facilities(db=self.db, _current_user=self.user_b)
        self.assertEqual([facility.name for facility in facilities], ["Pádel B"])

    def test_otp_request_resolves_household_inside_selected_community(self) -> None:
        previous_dev_setting = settings.DEV_PRINT_OTP
        try:
            settings.DEV_PRINT_OTP = False
            request_otp(
                payload=RequestOTPIn(
                    community_slug="community-b",
                    house_code="bloque 18 3ºb",
                    email=self.user_b.email,
                ),
                db=self.db,
            )
        finally:
            settings.DEV_PRINT_OTP = previous_dev_setting
        otp = self.db.query(AuthOTP).one()
        audit = self.db.query(AuditLog).one()
        self.assertEqual(otp.community_id, self.community_b.id)
        self.assertEqual(audit.community_id, self.community_b.id)
        self.assertEqual(audit.household_id, self.household_b.id)

    def test_cross_community_facility_cannot_be_reserved(self) -> None:
        tomorrow_at_nine = (datetime.now() + timedelta(days=1)).replace(
            hour=9,
            minute=0,
            second=0,
            microsecond=0,
        )
        with self.assertRaises(HTTPException) as raised:
            create_reservation(
                payload=CreateReservationIn(
                    facility_id=self.facility_a.id,
                    start_at=tomorrow_at_nine,
                ),
                db=self.db,
                current_user=self.user_b,
            )
        self.assertEqual(raised.exception.status_code, 404)
        self.assertEqual(self.db.query(Reservation).count(), 0)

    def test_notification_from_other_community_is_not_addressable(self) -> None:
        notification = Notification(
            community_id=self.community_b.id,
            user_id=self.user_b.id,
            household_id=self.household_b.id,
            type="TEST",
            message="Solo para B",
        )
        self.db.add(notification)
        self.db.commit()

        with self.assertRaises(HTTPException) as raised:
            mark_notification_as_read(
                notification_id=notification.id,
                db=self.db,
                current_user=self.user_a,
            )
        self.assertEqual(raised.exception.status_code, 404)


if __name__ == "__main__":
    unittest.main()
