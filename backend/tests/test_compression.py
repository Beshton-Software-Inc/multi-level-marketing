"""
Tests for the 7-level MLM commission cascade with compression.

Compression rule
----------------
Walk all ancestors first, then for each of the 7 levels:
  - Natural earner exists          → assign normally
  - Chain topped out (level > depth) → compress to topmost ancestor
  - No upline at all               → WinWinLaw retains (no Commission row written)
"""
from decimal import Decimal

import pytest

from app.models import Commission
from app.services.mlm_service import (
    DEFAULT_COMMISSION_RATES,
    calculate_and_create_commissions,
    preview_commission_breakdown,
)
from tests.helpers import make_affiliate, make_team, make_membership


# ── chain fixtures ────────────────────────────────────────────────────────────

@pytest.fixture
def chain_1_deep(db):
    """A → B: buyer uses B's code. Only A is in the upline (1 level)."""
    A = make_affiliate(db, "A", "a@test.com")
    B = make_affiliate(db, "B", "b@test.com", referred_by=A)
    return {"A": A, "buyer": B}


@pytest.fixture
def chain_3_deep(db):
    """A → B → C → D: buyer uses D's code. Upline = [C, B, A] (3 levels)."""
    A = make_affiliate(db, "A", "a@test.com")
    B = make_affiliate(db, "B", "b@test.com", referred_by=A)
    C = make_affiliate(db, "C", "c@test.com", referred_by=B)
    D = make_affiliate(db, "D", "d@test.com", referred_by=C)
    return {"A": A, "B": B, "C": C, "buyer": D}


@pytest.fixture
def chain_7_deep(db):
    """A → B → C → D → E → F → G → H: buyer uses H's code. Full 7-level upline."""
    prev = None
    affiliates = {}
    for letter in "ABCDEFGH":
        aff = make_affiliate(db, letter, f"{letter.lower()}@test.com", referred_by=prev)
        affiliates[letter] = aff
        prev = aff
    return affiliates   # buyer = H


@pytest.fixture
def no_upline(db):
    """A has no referrer — no upline at all."""
    A = make_affiliate(db, "A", "a@test.com")
    return {"buyer": A}


# ── calculate_and_create_commissions ─────────────────────────────────────────

class TestCompressionCascade:

    def test_1_deep_chain_all_7_levels_go_to_top_ancestor(self, db, chain_1_deep):
        """A is the only ancestor. L1 is natural; L2-L7 compress to A."""
        A = chain_1_deep["A"]

        calculate_and_create_commissions(
            new_affiliate_id=chain_1_deep["buyer"].id,
            subscription_amount=Decimal("100"),
            db=db,
        )

        a_tiers = sorted(
            c.tier for c in db.query(Commission).filter(Commission.earner_id == A.id)
        )
        assert a_tiers == [1, 2, 3, 4, 5, 6, 7]

    def test_3_deep_chain_natural_earners_for_L1_L2_L3(self, db, chain_3_deep):
        """L1=C, L2=B, L3=A all receive their tiers naturally."""
        calculate_and_create_commissions(
            new_affiliate_id=chain_3_deep["buyer"].id,
            subscription_amount=Decimal("100"),
            db=db,
        )

        for expected_earner, tier in [(chain_3_deep["C"], 1),
                                      (chain_3_deep["B"], 2),
                                      (chain_3_deep["A"], 3)]:
            row = db.query(Commission).filter(
                Commission.earner_id == expected_earner.id,
                Commission.tier == tier,
            ).first()
            assert row is not None, f"Expected natural earner at L{tier}"

    def test_3_deep_chain_L4_to_L7_compressed_to_topmost_ancestor(self, db, chain_3_deep):
        """Levels 4-7 have no natural earner and must compress to A."""
        A = chain_3_deep["A"]

        calculate_and_create_commissions(
            new_affiliate_id=chain_3_deep["buyer"].id,
            subscription_amount=Decimal("100"),
            db=db,
        )

        a_tiers = sorted(
            c.tier for c in db.query(Commission).filter(Commission.earner_id == A.id)
        )
        # A earns L3 naturally + L4-L7 compressed
        assert a_tiers == [3, 4, 5, 6, 7]

    def test_3_deep_chain_total_commission_count_is_7(self, db, chain_3_deep):
        calculate_and_create_commissions(
            new_affiliate_id=chain_3_deep["buyer"].id,
            subscription_amount=Decimal("100"),
            db=db,
        )
        assert db.query(Commission).count() == 7

    def test_no_upline_zero_commissions_written(self, db, no_upline):
        """No Commission rows — all levels retained by WinWinLaw."""
        calculate_and_create_commissions(
            new_affiliate_id=no_upline["buyer"].id,
            subscription_amount=Decimal("100"),
            db=db,
        )
        assert db.query(Commission).count() == 0

    def test_7_deep_chain_every_level_has_natural_earner(self, db, chain_7_deep):
        """Full chain: G=L1, F=L2, E=L3, D=L4, C=L5, B=L6, A=L7."""
        calculate_and_create_commissions(
            new_affiliate_id=chain_7_deep["H"].id,
            subscription_amount=Decimal("100"),
            db=db,
        )

        for tier, letter in enumerate("GFEDCBA", start=1):
            row = db.query(Commission).filter(
                Commission.earner_id == chain_7_deep[letter].id,
                Commission.tier == tier,
            ).first()
            assert row is not None, f"{letter} should be natural earner at L{tier}"

    def test_7_deep_chain_no_commission_is_compressed(self, db, chain_7_deep):
        calculate_and_create_commissions(
            new_affiliate_id=chain_7_deep["H"].id,
            subscription_amount=Decimal("100"),
            db=db,
        )
        # Every ancestor earns exactly one tier
        assert db.query(Commission).count() == 7


class TestCompressionAmounts:

    def test_3_deep_chain_L1_amount_with_50pct_team_rate(self, db, chain_3_deep):
        """$199 subscription, 50% team rate → team_share=$99.50.
        L1 (C) earns $99.50 × 20% = $19.90."""
        calculate_and_create_commissions(
            new_affiliate_id=chain_3_deep["buyer"].id,
            subscription_amount=Decimal("199"),
            db=db,
            team_commission_rate=Decimal("50"),
        )

        team_share = (Decimal("199") * Decimal("50") / Decimal("100")).quantize(Decimal("0.01"))
        expected_l1 = (team_share * DEFAULT_COMMISSION_RATES[1]).quantize(Decimal("0.01"))

        l1 = db.query(Commission).filter(
            Commission.earner_id == chain_3_deep["C"].id,
            Commission.tier == 1,
        ).first()
        assert l1.amount == expected_l1

    def test_topmost_ancestor_receives_sum_of_compressed_tiers(self, db, chain_3_deep):
        """A receives natural L3 + compressed L4-L7. Total must equal sum of those rates."""
        A = chain_3_deep["A"]

        calculate_and_create_commissions(
            new_affiliate_id=chain_3_deep["buyer"].id,
            subscription_amount=Decimal("100"),
            db=db,
        )

        a_total = sum(
            c.amount
            for c in db.query(Commission).filter(Commission.earner_id == A.id)
        )
        expected = sum(
            (Decimal("100") * DEFAULT_COMMISSION_RATES[lvl]).quantize(Decimal("0.01"))
            for lvl in [3, 4, 5, 6, 7]
        )
        assert a_total == expected


class TestSnapshotColumns:

    def test_subscription_amount_snapshotted_on_every_row(self, db, chain_3_deep):
        calculate_and_create_commissions(
            new_affiliate_id=chain_3_deep["buyer"].id,
            subscription_amount=Decimal("199"),
            db=db,
            team_commission_rate=Decimal("50"),
        )
        for c in db.query(Commission).all():
            assert c.subscription_amount == Decimal("199")

    def test_team_allocation_pct_snapshotted_on_every_row(self, db, chain_3_deep):
        calculate_and_create_commissions(
            new_affiliate_id=chain_3_deep["buyer"].id,
            subscription_amount=Decimal("100"),
            db=db,
            team_commission_rate=Decimal("40"),
        )
        for c in db.query(Commission).all():
            assert c.team_allocation_pct == Decimal("40")

    def test_changing_team_rate_does_not_alter_past_commissions(self, db, chain_3_deep):
        """Core snapshot test: old rows must not be affected by a later rate change.

        We simulate this by running commissions at 50%, then running again at 40%,
        and verifying the first batch still shows 50%.
        """
        buyer = chain_3_deep["buyer"]

        calculate_and_create_commissions(
            new_affiliate_id=buyer.id,
            subscription_amount=Decimal("100"),
            db=db,
            team_commission_rate=Decimal("50"),
        )

        first_batch_ids = [c.id for c in db.query(Commission).all()]

        # "Rate change" — second billing cycle uses 40%
        calculate_and_create_commissions(
            new_affiliate_id=buyer.id,
            subscription_amount=Decimal("100"),
            db=db,
            team_commission_rate=Decimal("40"),
        )

        for c in db.query(Commission).filter(Commission.id.in_(first_batch_ids)):
            assert c.team_allocation_pct == Decimal("50"), (
                "Old commissions must not reflect the new rate"
            )


# ── preview_commission_breakdown ─────────────────────────────────────────────

class TestPreviewBreakdown:

    def test_returns_7_rows(self, db, chain_3_deep):
        rows = preview_commission_breakdown(
            buyer_affiliate_id=chain_3_deep["buyer"].id,
            subscription_amount=Decimal("100"),
            db=db,
        )
        assert len(rows) == 7

    def test_L1_to_L3_not_compressed(self, db, chain_3_deep):
        rows = preview_commission_breakdown(
            buyer_affiliate_id=chain_3_deep["buyer"].id,
            subscription_amount=Decimal("100"),
            db=db,
        )
        for row in rows[:3]:
            assert row["compressed"] is False

    def test_L4_to_L7_marked_compressed(self, db, chain_3_deep):
        rows = preview_commission_breakdown(
            buyer_affiliate_id=chain_3_deep["buyer"].id,
            subscription_amount=Decimal("100"),
            db=db,
        )
        for row in rows[3:]:
            assert row["compressed"] is True

    def test_compressed_from_level_equals_chain_depth(self, db, chain_3_deep):
        rows = preview_commission_breakdown(
            buyer_affiliate_id=chain_3_deep["buyer"].id,
            subscription_amount=Decimal("100"),
            db=db,
        )
        for row in rows[3:]:
            assert row["compressed_from_level"] == 3

    def test_no_upline_all_rows_retained_by_platform(self, db, no_upline):
        rows = preview_commission_breakdown(
            buyer_affiliate_id=no_upline["buyer"].id,
            subscription_amount=Decimal("100"),
            db=db,
        )
        assert len(rows) == 7
        assert all(row["retained_by_platform"] is True for row in rows)

    def test_preview_does_not_write_to_db(self, db, chain_3_deep):
        preview_commission_breakdown(
            buyer_affiliate_id=chain_3_deep["buyer"].id,
            subscription_amount=Decimal("100"),
            db=db,
        )
        assert db.query(Commission).count() == 0
