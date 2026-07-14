"""Regression tests for the total_earnings race condition.

Both write sites (the commission cascade in mlm_service.py and the manual
admin commission endpoint) used to do `earner.total_earnings = (earner.total_earnings
or 0) + amount` in Python — a read-modify-write. Two concurrent transactions
crediting the same affiliate (e.g. two webhook deliveries that share an
upline ancestor) could both read the same starting balance and one credit
would clobber the other.

The fix replaced both with a single atomic `UPDATE ... SET total_earnings =
coalesce(total_earnings, 0) + amount` so the increment is computed by the
database from whatever the row's *current* value is, not from a Python
attribute that might be stale.

These tests prove that by deliberately staling the ORM's cached copy of an
affiliate's total_earnings (simulating what a concurrent transaction's
already-committed credit would look like to this process) and checking the
final balance reflects both credits rather than losing one.
"""
from decimal import Decimal

from sqlalchemy import text

from app.models import Affiliate
from app.services.mlm_service import calculate_and_create_commissions
from tests.helpers import auth_headers, make_affiliate


def _make_stale(db, affiliate, new_value):
    """Update the row directly in SQL, bypassing the ORM identity map, so
    `affiliate.total_earnings` in Python keeps showing the old cached value
    even though the DB row has already moved on — exactly what a concurrent
    transaction's committed write would leave behind.
    """
    db.execute(
        text("UPDATE affiliates SET total_earnings = :v WHERE id = :id"),
        {"v": str(new_value), "id": affiliate.id},
    )


class TestCommissionCascadeAtomicCredit:

    def test_credit_is_added_to_current_db_value_not_stale_python_value(self, db):
        earner = make_affiliate(db, "Earner", "atomic_earner@test.com")
        buyer = make_affiliate(db, "Buyer", "atomic_buyer@test.com", referred_by=earner)

        _make_stale(db, earner, Decimal("50"))
        assert earner.total_earnings == Decimal("0")  # stale in-memory value

        calculate_and_create_commissions(
            new_affiliate_id=buyer.id,
            subscription_amount=Decimal("100"),
            db=db,
        )

        fresh = db.query(Affiliate).filter(Affiliate.id == earner.id).first()
        db.refresh(fresh)
        # earner is buyer's only ancestor, so all 7 levels compress to it —
        # 50% of $100 = $50 (sum of DEFAULT_COMMISSION_RATES). Correct result
        # is the $50 already committed elsewhere plus this $50 — not $50 alone.
        assert fresh.total_earnings == Decimal("100.00")


class TestManualCommissionAtomicCredit:

    def test_admin_add_commission_credits_current_db_value(self, db, client):
        admin = make_affiliate(db, "Admin", "atomic_admin@test.com", is_admin=True)
        earner = make_affiliate(db, "Earner", "atomic_earner2@test.com")

        _make_stale(db, earner, Decimal("50"))
        assert earner.total_earnings == Decimal("0")

        resp = client.post(
            "/api/admin/commission",
            json={"affiliate_email": earner.email, "amount": "20", "description": "bonus"},
            headers=auth_headers(admin),
        )
        assert resp.status_code == 200

        fresh = db.query(Affiliate).filter(Affiliate.id == earner.id).first()
        db.refresh(fresh)
        assert fresh.total_earnings == Decimal("70.00")
