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
    CommunityPolicy,
    Facility,
    Household,
    Notification,
    Reservation,
    UnlockProposal,
    User,
)
from app.routers.auth import request_otp
from app.routers.facilities import list_facilities
from app.routers.community import read_community_policy
from app.routers.notifications import mark_notification_as_read
from app.routers.reservations import create_reservation
from app.routers.unlock import cast_unlock_vote
from app.schemas import CreateReservationIn, RequestOTPIn, UnlockVoteIn
from app.services.rules import can_cancel_reservation, is_within_booking_window


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

        self.community_a = Community(
            slug="community-a",
            name="Comunidad A",
            policy=CommunityPolicy(
                booking_window_days=7,
                cancellation_limit_hours=4,
            ),
        )
        self.community_b = Community(
            slug="community-b",
            name="Comunidad B",
            policy=CommunityPolicy(
                booking_window_days=2,
                cancellation_limit_hours=24,
                unlock_voting_enabled=False,
            ),
        )
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

    def test_policy_endpoint_is_scoped_to_authenticated_community(self) -> None:
        policy = read_community_policy(db=self.db, current_user=self.user_b)
        self.assertEqual(policy.community_id, self.community_b.id)
        self.assertEqual(policy.booking_window_days, 2)
        self.assertFalse(policy.unlock_voting_enabled)

    def test_booking_window_can_differ_between_communities(self) -> None:
        now = datetime.now()
        start_at = now + timedelta(days=3)
        self.assertTrue(
            is_within_booking_window(start_at, now, self.community_a.policy)
        )
        self.assertFalse(
            is_within_booking_window(start_at, now, self.community_b.policy)
        )

    def test_cancellation_limit_can_differ_between_communities(self) -> None:
        now = datetime.now()
        start_at = now + timedelta(hours=12)
        self.assertTrue(
            can_cancel_reservation(start_at, now, self.community_a.policy)
        )
        self.assertFalse(
            can_cancel_reservation(start_at, now, self.community_b.policy)
        )

    def test_unlock_votes_are_rejected_when_disabled_for_community(self) -> None:
        now = datetime.now()
        proposal = UnlockProposal(
            community_id=self.community_b.id,
            target_household_id=self.household_b.id,
            created_by_user_id=self.user_b.id,
            reason="Revisión administrativa",
            status="OPEN",
            created_at=now,
            closes_at=now + timedelta(hours=48),
        )
        self.db.add(proposal)
        self.db.commit()

        with self.assertRaises(HTTPException) as raised:
            cast_unlock_vote(
                proposal_id=proposal.id,
                payload=UnlockVoteIn(vote="YES"),
                db=self.db,
                current_user=self.user_b,
            )
        self.assertEqual(raised.exception.status_code, 409)

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
