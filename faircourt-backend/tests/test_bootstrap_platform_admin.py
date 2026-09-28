import unittest

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db import Base
from app.models import Community, CommunityPolicy, Household, User, UserRole
from scripts.bootstrap_platform_admin import create_platform_admin


class BootstrapPlatformAdminTests(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(self.engine)
        self.db: Session = sessionmaker(bind=self.engine)()

    def tearDown(self) -> None:
        self.db.close()
        Base.metadata.drop_all(self.engine)
        self.engine.dispose()

    def test_creates_an_active_platform_admin_once(self) -> None:
        self.assertTrue(create_platform_admin(self.db, "Admin@Example.com"))
        self.assertFalse(create_platform_admin(self.db, "admin@example.com"))

        user = self.db.query(User).one()
        self.assertEqual(user.email, "admin@example.com")
        self.assertEqual(user.role, UserRole.PLATFORM_ADMIN.value)
        self.assertTrue(user.is_active)
        self.assertIsNone(user.community_id)
        self.assertIsNone(user.household_id)

    def test_does_not_elevate_an_existing_resident(self) -> None:
        community = Community(
            slug="faircourt",
            name="FairCourt",
            policy=CommunityPolicy(),
        )
        self.db.add(community)
        self.db.flush()
        household = Household(community_id=community.id, code="A1")
        self.db.add(household)
        self.db.flush()
        self.db.add(
            User(
                email="resident@example.com",
                role=UserRole.RESIDENT.value,
                community_id=community.id,
                household_id=household.id,
            )
        )
        self.db.commit()

        with self.assertRaisesRegex(ValueError, "no es administradora"):
            create_platform_admin(self.db, "resident@example.com")

        resident = self.db.query(User).one()
        self.assertEqual(resident.role, UserRole.RESIDENT.value)


if __name__ == "__main__":
    unittest.main()
