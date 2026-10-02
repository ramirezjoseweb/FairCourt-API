from __future__ import annotations

import unittest

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.config import settings
from app.db import Base
from app.models import Community, CommunityPolicy, Household
from scripts.bootstrap_production_communities import provision_communities


class BootstrapProductionCommunitiesTests(unittest.TestCase):
    def setUp(self) -> None:
        self.previous_env = settings.APP_ENV
        settings.APP_ENV = "production"
        self.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(self.engine)
        self.db = Session(self.engine)
        self.db.add(Community(slug="faircourt", name="Comunidad FairCourt", policy=CommunityPolicy()))
        self.db.commit()

    def tearDown(self) -> None:
        self.db.close()
        self.engine.dispose()
        settings.APP_ENV = self.previous_env

    def test_creates_real_communities_and_inactivates_empty_demo_once(self) -> None:
        provision_communities(self.db)
        provision_communities(self.db)
        communities = {row.slug: row for row in self.db.query(Community).all()}
        self.assertEqual(set(communities), {"faircourt", "gran-parque", "parque-venecia"})
        self.assertFalse(communities["faircourt"].is_active)
        self.assertTrue(communities["gran-parque"].is_active)
        self.assertTrue(communities["parque-venecia"].is_active)

    def test_does_not_inactivate_legacy_community_with_data(self) -> None:
        legacy = self.db.query(Community).filter(Community.slug == "faircourt").one()
        self.db.add(Household(community_id=legacy.id, code="DEMO-01"))
        self.db.commit()
        with self.assertRaises(RuntimeError):
            provision_communities(self.db)
        self.db.rollback()
        self.assertTrue(legacy.is_active)
        self.assertEqual(self.db.query(Community).count(), 1)


if __name__ == "__main__":
    unittest.main()
