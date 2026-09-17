from __future__ import annotations

import unittest
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
    Community,
    CommunityPolicy,
    Facility,
    Household,
    User,
    UserRole,
)
from app.routers.admin import (
    list_admin_communities,
    read_private_admin_audit,
    request_admin_otp,
    select_admin_community,
    verify_admin_otp,
)
from app.routers.audit import get_my_audit_logs
from app.schemas import AdminRequestOTPIn, AdminVerifyOTPIn
from app.security import create_access_token


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


if __name__ == "__main__":
    unittest.main()
