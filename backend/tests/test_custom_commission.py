"""
Tests for custom commission mode and retain_admin unassigned policy.

Custom mode
-----------
Teams can choose "default" (fixed platform rates) or "custom" (admin-defined
per-level % stored in custom_rate_l1..l7).  build_effective_rates() translates
the model into the Dict[int, Decimal] that mlm_service consumes.

retain_admin policy
-------------------
When a level has no natural earner (chain topped out), the unassigned
commission can go to:
  - topmost ancestor  (compress — the default)
  - team admin affiliate (retain_admin)
If retain_admin is chosen but the team has no admin_id, it silently falls back
to compress.
"""
from decimal import Decimal

import pytest

from app.models import Commission
from app.services.mlm_service import (
    DEFAULT_COMMISSION_RATES,
    build_effective_rates,
    calculate_and_create_commissions,
)
from tests.helpers import make_affiliate, make_team, make_membership


# ── build_effective_rates ─────────────────────────────────────────────────────

class TestBuildEffectiveRates:

    def test_no_team_returns_default_rates(self):
        rates = build_effective_rates(None)
        assert rates == DEFAULT_COMMISSION_RATES

    def test_default_mode_returns_platform_rates(self, db):
        team = make_team(db, commission_mode="default")
        rates = build_effective_rates(team)
        assert rates == DEFAULT_COMMISSION_RATES

    def test_custom_mode_returns_team_rates_divided_by_100(self, db):
        team = make_team(
            db,
            commission_mode="custom",
            custom_rate_l1=30,
            custom_rate_l2=10,
            custom_rate_l3=10,
            custom_rate_l4=5,
            custom_rate_l5=5,
            custom_rate_l6=5,
            custom_rate_l7=5,
        )
        rates = build_effective_rates(team)
        assert rates[1] == Decimal("0.30")
        assert rates[2] == Decimal("0.10")
        assert rates[7] == Decimal("0.05")

    def test_null_custom_rate_treated_as_zero(self, db):
        team = make_team(
            db,
            commission_mode="custom",
            custom_rate_l1=20,
            # l2-l7 are left NULL
        )
        rates = build_effective_rates(team)
        assert rates[1] == Decimal("0.20")
        for level in range(2, 8):
            assert rates[level] == Decimal("0")

    def test_default_mode_ignores_custom_rate_columns(self, db):
        """Even if custom_rate columns are populated, default mode should ignore them."""
        team = make_team(
            db,
            commission_mode="default",
            custom_rate_l1=99,
            custom_rate_l2=99,
        )
        rates = build_effective_rates(team)
        assert rates == DEFAULT_COMMISSION_RATES


# ── custom rates in commission amounts ───────────────────────────────────────

class TestCustomRateAmounts:

    def _chain_2_deep(self, db):
        """A → B → C: buyer=C, upline=[B, A]."""
        A = make_affiliate(db, "A", "a@test.com")
        B = make_affiliate(db, "B", "b@test.com", referred_by=A)
        C = make_affiliate(db, "C", "c@test.com", referred_by=B)
        return A, B, C

    def test_custom_rates_produce_correct_amounts(self, db):
        """L1=30%, L2=10%, others=0. $100 sub → B earns $30, A earns $10."""
        A, B, C = self._chain_2_deep(db)

        team = make_team(
            db,
            commission_mode="custom",
            custom_rate_l1=30,
            custom_rate_l2=10,
        )
        commission_rates = build_effective_rates(team)

        calculate_and_create_commissions(
            new_affiliate_id=C.id,
            subscription_amount=Decimal("100"),
            db=db,
            team_commission_rate=Decimal("100"),  # full amount goes to affiliates
            commission_rates=commission_rates,
        )

        b_l1 = db.query(Commission).filter(
            Commission.earner_id == B.id, Commission.tier == 1
        ).first()
        a_l2 = db.query(Commission).filter(
            Commission.earner_id == A.id, Commission.tier == 2
        ).first()

        assert b_l1 is not None
        assert a_l2 is not None
        assert b_l1.amount == Decimal("30.00")
        assert a_l2.amount == Decimal("10.00")

    def test_custom_zero_rate_creates_zero_amount_commission(self, db):
        """A level with rate 0 still writes a Commission row (to topmost ancestor
        via compression) but with amount=0.00."""
        A, B, C = self._chain_2_deep(db)

        # Only L1 is set; L2-L7 are 0.  A will receive compressed rows with $0.
        team = make_team(
            db,
            commission_mode="custom",
            custom_rate_l1=20,
        )
        commission_rates = build_effective_rates(team)

        calculate_and_create_commissions(
            new_affiliate_id=C.id,
            subscription_amount=Decimal("100"),
            db=db,
            commission_rates=commission_rates,
        )

        a_commissions = db.query(Commission).filter(Commission.earner_id == A.id).all()
        # A is the topmost ancestor; it receives L2 naturally + L3-L7 compressed.
        # All have rate 0 so amounts are $0.
        assert len(a_commissions) >= 1
        for c in a_commissions:
            assert c.amount == Decimal("0.00")


# ── retain_admin policy ───────────────────────────────────────────────────────

class TestRetainAdmin:

    def _chain_2_deep(self, db):
        """Returns (A, B, buyer) where A → B → buyer."""
        A = make_affiliate(db, "A", "a@test.com")
        B = make_affiliate(db, "B", "b@test.com", referred_by=A)
        buyer = make_affiliate(db, "Buyer", "buyer@test.com", referred_by=B)
        return A, B, buyer

    def test_unfilled_levels_go_to_admin_not_topmost_ancestor(self, db):
        """Chain depth=2 (A, B). L3-L7 have no natural earner.
        With retain_admin, they go to the admin affiliate, not A."""
        A, B, buyer = self._chain_2_deep(db)

        # Make a separate admin affiliate not in the upline
        admin = make_affiliate(db, "Admin", "admin@test.com")

        team = make_team(db, unassigned_policy="retain_admin")
        make_membership(db, team, A, role="member")
        make_membership(db, team, B, role="member")

        calculate_and_create_commissions(
            new_affiliate_id=buyer.id,
            subscription_amount=Decimal("100"),
            db=db,
            unassigned_policy="retain_admin",
            team_admin_id=admin.id,
        )

        admin_tiers = sorted(
            c.tier for c in db.query(Commission).filter(Commission.earner_id == admin.id)
        )
        # Levels 3-7 should go to admin
        assert admin_tiers == [3, 4, 5, 6, 7]

        # A should NOT have received L3-L7
        a_tiers = [
            c.tier for c in db.query(Commission).filter(Commission.earner_id == A.id)
        ]
        assert all(t not in a_tiers for t in [3, 4, 5, 6, 7])

    def test_retain_admin_does_not_override_natural_earners(self, db):
        """Natural earners at L1 and L2 are never replaced by the admin."""
        A, B, buyer = self._chain_2_deep(db)
        admin = make_affiliate(db, "Admin", "admin@test.com")

        calculate_and_create_commissions(
            new_affiliate_id=buyer.id,
            subscription_amount=Decimal("100"),
            db=db,
            unassigned_policy="retain_admin",
            team_admin_id=admin.id,
        )

        # B earns L1, A earns L2 — admin should not have either
        b_l1 = db.query(Commission).filter(
            Commission.earner_id == B.id, Commission.tier == 1
        ).first()
        a_l2 = db.query(Commission).filter(
            Commission.earner_id == A.id, Commission.tier == 2
        ).first()
        admin_l1 = db.query(Commission).filter(
            Commission.earner_id == admin.id, Commission.tier == 1
        ).first()
        admin_l2 = db.query(Commission).filter(
            Commission.earner_id == admin.id, Commission.tier == 2
        ).first()

        assert b_l1 is not None
        assert a_l2 is not None
        assert admin_l1 is None
        assert admin_l2 is None

    def test_retain_admin_falls_back_to_compress_when_admin_id_is_none(self, db):
        """If team_admin_id is None, unfilled levels compress to topmost ancestor."""
        A, B, buyer = self._chain_2_deep(db)

        calculate_and_create_commissions(
            new_affiliate_id=buyer.id,
            subscription_amount=Decimal("100"),
            db=db,
            unassigned_policy="retain_admin",
            team_admin_id=None,  # no admin configured
        )

        # A is the topmost ancestor; it should receive L2 (natural) + L3-L7 (compressed)
        a_tiers = sorted(
            c.tier for c in db.query(Commission).filter(Commission.earner_id == A.id)
        )
        assert a_tiers == [2, 3, 4, 5, 6, 7]
