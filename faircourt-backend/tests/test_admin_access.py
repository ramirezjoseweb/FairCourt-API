from __future__ import annotations

import unittest
from datetime import datetime, timedelta
from unittest.mock import patch

from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from jose import jwt
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.config import settings
from app.db import Base
from app.deps import get_current_user, require_platform_admin, require_resident
from app.models import (
    AuditLog,
    AuditVisibility,
    AuthOTP,
    Community,
    CommunityPolicy,
    Facility,
    Household,
    Reservation,
    User,
    UserRole,
)
from app.routers.admin import (
    create_admin_household,
    create_admin_facility,
    list_admin_households,
    list_admin_communities,
    list_admin_facilities,
    read_admin_community_policy,
    read_private_admin_audit,
    request_admin_otp,
    select_admin_community,
    update_admin_facility,
    update_admin_household,
    update_admin_household_access,
    update_admin_basic_policy,
    verify_admin_otp,
)
from app.routers.audit import get_my_audit_logs
from app.schemas import (
    AdminBasicPolicyUpdateIn,
    AdminFacilityWriteIn,
    AdminHouseholdCreateIn,
    AdminHouseholdAccessUpdateIn,
    AdminHouseholdUpdateIn,
    AdminRequestOTPIn,
    AdminVerifyOTPIn,
)
from app.security import create_access_token
from app.security import hash_secret


class AdminAccessTests(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(self.engine)
        self.db: Session = sessionmaker(bind=self.engine)()

        self.community_a = Community(
            slug="gran-parque",
            name="Gran Parque",
            policy=CommunityPolicy(),
        )
        self.community_b = Community(
            slug="community-b",
            name="Comunidad B",
            policy=CommunityPolicy(),
        )
        self.db.add_all([self.community_a, self.community_b])
        self.db.flush()
        self.household = Household(
            community_id=self.community_a.id,
            code="GRP0001",
        )
        self.facility = Facility(
            community_id=self.community_a.id,
            slug="padel",
            name="Pádel",
            category="Deporte",
        )
        self.facility_b = Facility(
            community_id=self.community_b.id,
            slug="padel",
            name="Pádel B",
            category="Deporte",
        )
        self.db.add_all([self.household, self.facility, self.facility_b])
        self.db.flush()
        self.resident = User(
            email="resident@example.com",
            role=UserRole.RESIDENT.value,
            community_id=self.community_a.id,
            household_id=self.household.id,
        )
        self.admin = User(
            email="admin@example.com",
            role=UserRole.PLATFORM_ADMIN.value,
            community_id=None,
            household_id=None,
        )
        self.db.add_all([self.resident, self.admin])
        self.db.commit()

    def tearDown(self) -> None:
        self.db.close()
        self.engine.dispose()

    def test_resident_cannot_gain_platform_admin_permissions(self) -> None:
        with self.assertRaises(HTTPException) as raised:
            require_platform_admin(current_user=self.resident)
        self.assertEqual(raised.exception.status_code, 403)

        forged_token, _ = create_access_token(
            subject=self.resident.email,
            role=UserRole.PLATFORM_ADMIN.value,
        )
        with self.assertRaises(HTTPException) as forged:
            get_current_user(
                credentials=HTTPAuthorizationCredentials(
                    scheme="Bearer",
                    credentials=forged_token,
                ),
                db=self.db,
            )
        self.assertEqual(forged.exception.status_code, 401)

    def test_platform_admin_cannot_use_resident_operations(self) -> None:
        with self.assertRaises(HTTPException) as raised:
            require_resident(current_user=self.admin)
        self.assertEqual(raised.exception.status_code, 403)

        wrongly_scoped_token, _ = create_access_token(
            subject=self.admin.email,
            community_id=self.community_a.id,
            role=UserRole.PLATFORM_ADMIN.value,
        )
        with self.assertRaises(HTTPException) as scoped:
            get_current_user(
                credentials=HTTPAuthorizationCredentials(
                    scheme="Bearer",
                    credentials=wrongly_scoped_token,
                ),
                db=self.db,
            )
        self.assertEqual(scoped.exception.status_code, 401)

    def test_admin_otp_issues_role_bound_token(self) -> None:
        previous_dev_setting = settings.DEV_PRINT_OTP
        settings.DEV_PRINT_OTP = False
        try:
            with patch("app.routers.admin.gen_otp", return_value="123456"):
                request_admin_otp(
                    payload=AdminRequestOTPIn(email=self.admin.email),
                    db=self.db,
                )
            response = verify_admin_otp(
                payload=AdminVerifyOTPIn(
                    email=self.admin.email,
                    otp="123456",
                ),
                db=self.db,
            )
        finally:
            settings.DEV_PRINT_OTP = previous_dev_setting

        payload = jwt.decode(
            response["access_token"],
            settings.SECRET_KEY,
            algorithms=[settings.JWT_ALG],
        )
        self.assertEqual(payload["role"], UserRole.PLATFORM_ADMIN.value)
        self.assertNotIn("community_id", payload)

    def test_unknown_admin_email_does_not_create_otp(self) -> None:
        response = request_admin_otp(
            payload=AdminRequestOTPIn(email="unknown@example.com"),
            db=self.db,
        )
        self.assertIn("Si el correo", response["message"])
        self.assertEqual(self.db.query(AuditLog).count(), 0)

    def test_community_selection_is_explicit_and_privately_audited(self) -> None:
        communities = list_admin_communities(db=self.db, _admin=self.admin)
        by_slug = {community["slug"]: community for community in communities}
        self.assertEqual(by_slug["gran-parque"]["household_count"], 1)
        self.assertEqual(by_slug["community-b"]["household_count"], 0)
        self.assertEqual(by_slug["gran-parque"]["facility_count"], 1)
        self.assertEqual(by_slug["community-b"]["facility_count"], 1)

        selected = select_admin_community(
            community_id=self.community_a.id,
            db=self.db,
            admin=self.admin,
        )
        self.assertEqual(selected["slug"], "gran-parque")

        private_entries = read_private_admin_audit(
            community_id=self.community_a.id,
            db=self.db,
            _admin=self.admin,
        )
        self.assertEqual(len(private_entries), 1)
        self.assertEqual(
            private_entries[0].visibility,
            AuditVisibility.ADMIN.value,
        )
        self.assertEqual(
            get_my_audit_logs(db=self.db, current_user=self.resident),
            [],
        )

    def test_admin_manages_facilities_only_inside_selected_community(self) -> None:
        payload = AdminFacilityWriteIn(
            slug="tenis",
            name="Tenis",
            category="Deporte",
            description="Pista de tenis comunitaria",
            priority=20,
            opening_hour=8,
            closing_hour=23,
            slot_duration_minutes=90,
        )
        created = create_admin_facility(
            community_id=self.community_b.id,
            payload=payload,
            db=self.db,
            admin=self.admin,
        )
        self.assertEqual(created.community_id, self.community_b.id)
        self.assertEqual(created.slug, "tenis")

        facilities_b = list_admin_facilities(
            community_id=self.community_b.id,
            db=self.db,
            _admin=self.admin,
        )
        self.assertEqual([row.slug for row in facilities_b], ["tenis", "padel"])

        with self.assertRaises(HTTPException) as crossed:
            update_admin_facility(
                community_id=self.community_a.id,
                facility_id=created.id,
                payload=payload,
                db=self.db,
                admin=self.admin,
            )
        self.assertEqual(crossed.exception.status_code, 404)

        with self.assertRaises(HTTPException) as duplicate:
            create_admin_facility(
                community_id=self.community_b.id,
                payload=payload,
                db=self.db,
                admin=self.admin,
            )
        self.assertEqual(duplicate.exception.status_code, 409)

        updated = update_admin_facility(
            community_id=self.community_b.id,
            facility_id=created.id,
            payload=AdminFacilityWriteIn(
                **{
                    **payload.model_dump(),
                    "name": "Tenis renovado",
                    "is_active": False,
                }
            ),
            db=self.db,
            admin=self.admin,
        )
        self.assertEqual(updated.name, "Tenis renovado")
        self.assertFalse(updated.is_active)

        events = [
            row.event
            for row in read_private_admin_audit(
                community_id=self.community_b.id,
                db=self.db,
                _admin=self.admin,
            )
        ]
        self.assertEqual(
            events,
            ["ADMIN_FACILITY_UPDATED", "ADMIN_FACILITY_CREATED"],
        )
        self.assertEqual(get_my_audit_logs(db=self.db, current_user=self.resident), [])

    def test_admin_creates_and_lists_households_only_in_target_community(self) -> None:
        created = create_admin_household(
            community_id=self.community_b.id,
            payload=AdminHouseholdCreateIn(code="  GRP0001  "),
            db=self.db,
            admin=self.admin,
        )
        self.assertEqual(created["community_id"], self.community_b.id)
        self.assertEqual(created["code"], "GRP0001")
        self.assertIsNone(created["resident_email"])

        households_a = list_admin_households(
            community_id=self.community_a.id,
            db=self.db,
            _admin=self.admin,
        )
        households_b = list_admin_households(
            community_id=self.community_b.id,
            db=self.db,
            _admin=self.admin,
        )
        self.assertEqual([row["code"] for row in households_a], ["GRP0001"])
        self.assertEqual([row["code"] for row in households_b], ["GRP0001"])
        self.assertEqual(households_a[0]["resident_email"], self.resident.email)

        with self.assertRaises(HTTPException) as duplicate:
            create_admin_household(
                community_id=self.community_b.id,
                payload=AdminHouseholdCreateIn(code="grp0001"),
                db=self.db,
                admin=self.admin,
            )
        self.assertEqual(duplicate.exception.status_code, 409)

        private_entries = read_private_admin_audit(
            community_id=self.community_b.id,
            db=self.db,
            _admin=self.admin,
        )
        self.assertEqual(
            [entry.event for entry in private_entries],
            ["ADMIN_HOUSEHOLD_CREATED"],
        )
        self.assertEqual(get_my_audit_logs(db=self.db, current_user=self.resident), [])

    def test_admin_edits_and_deactivates_household_without_cancelling_reservations(self) -> None:
        start_at = datetime.now() + timedelta(days=1)
        reservation = Reservation(
            community_id=self.community_a.id,
            household_id=self.household.id,
            facility_id=self.facility.id,
            start_at=start_at,
            end_at=start_at + timedelta(hours=1),
            status="ACTIVE",
        )
        self.db.add(reservation)
        self.db.commit()
        resident_token, _ = create_access_token(
            subject=self.resident.email,
            community_id=self.community_a.id,
            role=UserRole.RESIDENT.value,
        )

        updated = update_admin_household(
            community_id=self.community_a.id,
            household_id=self.household.id,
            payload=AdminHouseholdUpdateIn(
                code="GRP 0001 renovado",
                is_active=False,
            ),
            db=self.db,
            admin=self.admin,
        )
        self.assertEqual(updated["code"], "GRP 0001 renovado")
        self.assertFalse(updated["is_active"])
        self.assertTrue(self.resident.is_active)
        self.assertEqual(self.db.get(Reservation, reservation.id).status, "ACTIVE")

        with self.assertRaises(HTTPException) as inactive_session:
            get_current_user(
                credentials=HTTPAuthorizationCredentials(
                    scheme="Bearer",
                    credentials=resident_token,
                ),
                db=self.db,
            )
        self.assertEqual(inactive_session.exception.status_code, 403)
        self.assertEqual(inactive_session.exception.detail, "La vivienda está inactiva.")

        with self.assertRaises(HTTPException) as crossed:
            update_admin_household(
                community_id=self.community_b.id,
                household_id=self.household.id,
                payload=AdminHouseholdUpdateIn(
                    code="No debe cambiar",
                    is_active=True,
                ),
                db=self.db,
                admin=self.admin,
            )
        self.assertEqual(crossed.exception.status_code, 404)

        reactivated = update_admin_household(
            community_id=self.community_a.id,
            household_id=self.household.id,
            payload=AdminHouseholdUpdateIn(
                code="GRP 0001 renovado",
                is_active=True,
            ),
            db=self.db,
            admin=self.admin,
        )
        self.assertTrue(reactivated["is_active"])
        authenticated = get_current_user(
            credentials=HTTPAuthorizationCredentials(
                scheme="Bearer",
                credentials=resident_token,
            ),
            db=self.db,
        )
        self.assertEqual(authenticated.id, self.resident.id)

        events = [
            entry.event
            for entry in read_private_admin_audit(
                community_id=self.community_a.id,
                db=self.db,
                _admin=self.admin,
            )
        ]
        self.assertEqual(
            events,
            ["ADMIN_HOUSEHOLD_ACTIVATED", "ADMIN_HOUSEHOLD_UPDATED"],
        )

    def test_admin_reassigns_household_access_without_moving_history(self) -> None:
        start_at = datetime.now() + timedelta(days=1)
        reservation = Reservation(
            community_id=self.community_a.id,
            household_id=self.household.id,
            facility_id=self.facility.id,
            start_at=start_at,
            end_at=start_at + timedelta(hours=1),
            status="ACTIVE",
        )
        pending_otp = AuthOTP(
            community_id=self.community_a.id,
            email=self.resident.email,
            purpose="RESIDENT",
            otp_hash=hash_secret("123456"),
            expires_at=datetime.now() + timedelta(minutes=10),
        )
        self.db.add_all([reservation, pending_otp])
        self.db.commit()
        resident_id = self.resident.id
        old_token, _ = create_access_token(
            subject=self.resident.email,
            community_id=self.community_a.id,
            role=UserRole.RESIDENT.value,
        )

        updated = update_admin_household_access(
            community_id=self.community_a.id,
            household_id=self.household.id,
            payload=AdminHouseholdAccessUpdateIn(email="nuevo@example.com"),
            db=self.db,
            admin=self.admin,
        )
        self.assertEqual(updated["resident_email"], "nuevo@example.com")
        resident = self.db.get(User, resident_id)
        self.assertEqual(resident.email, "nuevo@example.com")
        self.assertEqual(resident.household_id, self.household.id)
        self.assertTrue(resident.is_active)
        self.assertEqual(self.db.get(Reservation, reservation.id).status, "ACTIVE")
        self.assertIsNotNone(self.db.get(AuthOTP, pending_otp.id).used_at)

        with self.assertRaises(HTTPException) as old_session:
            get_current_user(
                credentials=HTTPAuthorizationCredentials(
                    scheme="Bearer",
                    credentials=old_token,
                ),
                db=self.db,
            )
        self.assertEqual(old_session.exception.status_code, 401)

        with self.assertRaises(HTTPException) as same_email:
            update_admin_household_access(
                community_id=self.community_a.id,
                household_id=self.household.id,
                payload=AdminHouseholdAccessUpdateIn(email="nuevo@example.com"),
                db=self.db,
                admin=self.admin,
            )
        self.assertEqual(same_email.exception.status_code, 409)

        with self.assertRaises(HTTPException) as crossed:
            update_admin_household_access(
                community_id=self.community_b.id,
                household_id=self.household.id,
                payload=AdminHouseholdAccessUpdateIn(email="otro@example.com"),
                db=self.db,
                admin=self.admin,
            )
        self.assertEqual(crossed.exception.status_code, 404)

        entries = read_private_admin_audit(
            community_id=self.community_a.id,
            db=self.db,
            _admin=self.admin,
        )
        self.assertEqual(entries[0].event, "ADMIN_HOUSEHOLD_ACCESS_UPDATED")
        self.assertNotIn("nuevo@example.com", entries[0].metadata_json)

    def test_admin_assigns_access_to_unclaimed_household(self) -> None:
        unclaimed = Household(
            community_id=self.community_b.id,
            code="B-SIN-CUENTA",
        )
        self.db.add(unclaimed)
        self.db.commit()

        updated = update_admin_household_access(
            community_id=self.community_b.id,
            household_id=unclaimed.id,
            payload=AdminHouseholdAccessUpdateIn(email="asignado@example.com"),
            db=self.db,
            admin=self.admin,
        )
        self.assertEqual(updated["resident_email"], "asignado@example.com")
        self.assertEqual(unclaimed.user.email, "asignado@example.com")
        entries = read_private_admin_audit(
            community_id=self.community_b.id,
            db=self.db,
            _admin=self.admin,
        )
        self.assertEqual(entries[0].event, "ADMIN_HOUSEHOLD_ACCESS_ASSIGNED")

    def test_admin_updates_basic_policy_only_for_target_community(self) -> None:
        updated = update_admin_basic_policy(
            community_id=self.community_b.id,
            payload=AdminBasicPolicyUpdateIn(
                booking_window_days=14,
                max_active_reservations_per_day=2,
                max_active_reservations_per_week=4,
                cancellation_limit_hours=12,
            ),
            db=self.db,
            admin=self.admin,
        )
        self.assertEqual(updated.booking_window_days, 14)
        self.assertEqual(updated.max_active_reservations_per_day, 2)
        self.assertEqual(updated.max_active_reservations_per_week, 4)
        self.assertEqual(updated.cancellation_limit_hours, 12)

        untouched = read_admin_community_policy(
            community_id=self.community_a.id,
            db=self.db,
            _admin=self.admin,
        )
        self.assertEqual(untouched.booking_window_days, 7)
        self.assertEqual(untouched.max_active_reservations_per_day, 1)
        self.assertEqual(untouched.max_active_reservations_per_week, 2)
        self.assertEqual(untouched.cancellation_limit_hours, 4)

        private_entries = read_private_admin_audit(
            community_id=self.community_b.id,
            db=self.db,
            _admin=self.admin,
        )
        self.assertEqual(
            [entry.event for entry in private_entries],
            ["ADMIN_BASIC_POLICY_UPDATED"],
        )
        self.assertEqual(get_my_audit_logs(db=self.db, current_user=self.resident), [])


if __name__ == "__main__":
    unittest.main()
