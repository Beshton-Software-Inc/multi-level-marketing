"""Tests for get_team_members and get_affiliate_stats — previously untested
parts of mlm_service.py (the commission cascade itself is covered in
test_compression.py / test_custom_commission.py)."""
from decimal import Decimal

from app.services.mlm_service import get_affiliate_stats, get_team_members
from tests.helpers import make_affiliate, make_commission


class TestGetTeamMembers:

    def test_no_downline_returns_empty(self, db):
        aff = make_affiliate(db, "Solo", "solo_stats@test.com")
        db.commit()
        assert get_team_members(aff.id, db) == []

    def test_multi_level_downline_depth_and_order(self, db):
        # A -> B -> C, A -> D (two branches, mixed depth)
        A = make_affiliate(db, "A", "a_stats@test.com")
        B = make_affiliate(db, "B", "b_stats@test.com", referred_by=A)
        C = make_affiliate(db, "C", "c_stats@test.com", referred_by=B)
        D = make_affiliate(db, "D", "d_stats@test.com", referred_by=A)
        db.commit()

        members = get_team_members(A.id, db)
        by_name = {m["name"]: m for m in members}

        assert set(by_name) == {"B", "C", "D"}
        assert by_name["B"]["depth"] == 1
        assert by_name["D"]["depth"] == 1
        assert by_name["C"]["depth"] == 2
        assert by_name["B"]["direct_referrals"] == 1
        assert by_name["D"]["direct_referrals"] == 0

    def test_downline_of_a_leaf_is_empty(self, db):
        A = make_affiliate(db, "A", "a_leaf@test.com")
        B = make_affiliate(db, "B", "b_leaf@test.com", referred_by=A)
        db.commit()
        assert get_team_members(B.id, db) == []

    def test_recursion_stops_at_depth_10_guard(self, db):
        """recurse() bails out once depth > 10 — build a 12-level chain and
        confirm only the first 10 generations are returned."""
        root = make_affiliate(db, "Gen0", "gen0@test.com")
        prev = root
        for i in range(1, 13):
            prev = make_affiliate(db, f"Gen{i}", f"gen{i}@test.com", referred_by=prev)
        db.commit()

        members = get_team_members(root.id, db)
        depths = sorted(m["depth"] for m in members)
        assert depths == list(range(1, 11))


class TestGetAffiliateStats:

    def test_stats_reflect_direct_referrals_team_size_and_totals(self, db):
        A = make_affiliate(db, "A", "a_full@test.com", total_earnings=Decimal("42.50"))
        B = make_affiliate(db, "B", "b_full@test.com", referred_by=A)
        C = make_affiliate(db, "C", "c_full@test.com", referred_by=B)
        db.commit()

        stats = get_affiliate_stats(A.id, db)
        assert stats["direct_referrals"] == 1
        assert stats["team_size"] == 2  # B and C
        assert stats["total_earnings"] == Decimal("42.50")

    def test_pending_earnings_excludes_paid_commissions(self, db):
        A = make_affiliate(db, "A", "a_pending@test.com")
        make_commission(db, earner=A, amount=Decimal("10"), status="pending")
        make_commission(db, earner=A, amount=Decimal("999"), status="paid")
        db.commit()

        stats = get_affiliate_stats(A.id, db)
        assert stats["pending_earnings"] == Decimal("10")

    def test_stats_for_affiliate_with_no_activity(self, db):
        A = make_affiliate(db, "A", "a_none@test.com")
        db.commit()

        stats = get_affiliate_stats(A.id, db)
        assert stats["direct_referrals"] == 0
        assert stats["team_size"] == 0
        assert stats["total_earnings"] == Decimal("0")
        assert stats["pending_earnings"] == Decimal("0")
        assert stats["this_month_earnings"] == Decimal("0")
