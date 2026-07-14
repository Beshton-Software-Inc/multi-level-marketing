"""Tests for /api/affiliate (me, stats, team, earnings, payout requests)."""
from decimal import Decimal

from app.models import PayoutRequest
from tests.helpers import auth_headers, make_affiliate, make_commission


class TestRequiresAuth:

    def test_endpoints_reject_missing_token(self, client, db):
        for path in ("/api/affiliate/me", "/api/affiliate/stats", "/api/affiliate/team",
                     "/api/affiliate/earnings", "/api/affiliate/payouts"):
            resp = client.get(path)
            assert resp.status_code in (401, 403), path


class TestEarnings:

    def test_earnings_resolves_source_name(self, db, client):
        earner = make_affiliate(db, "Earner", "earner@test.com")
        buyer = make_affiliate(db, "Buyer", "buyer@test.com", referred_by=earner)
        make_commission(db, earner=earner, source=buyer, amount=Decimal("20.00"))
        db.commit()

        resp = client.get("/api/affiliate/earnings", headers=auth_headers(earner))
        assert resp.status_code == 200
        earnings = resp.json()["earnings"]
        assert len(earnings) == 1
        assert earnings[0]["source_name"] == "Buyer"

    def test_earnings_source_name_none_when_no_source(self, db, client):
        earner = make_affiliate(db, "Earner", "earner2@test.com")
        make_commission(db, earner=earner, source=None, amount=Decimal("5.00"))
        db.commit()

        resp = client.get("/api/affiliate/earnings", headers=auth_headers(earner))
        assert resp.status_code == 200
        assert resp.json()["earnings"][0]["source_name"] is None

    def test_earnings_pagination(self, db, client):
        earner = make_affiliate(db, "Earner", "earner3@test.com")
        for i in range(5):
            make_commission(db, earner=earner, amount=Decimal("1.00"))
        db.commit()

        resp = client.get("/api/affiliate/earnings?skip=0&limit=2", headers=auth_headers(earner))
        assert len(resp.json()["earnings"]) == 2

    def test_earnings_only_returns_own_commissions(self, db, client):
        earner = make_affiliate(db, "Earner", "earner4@test.com")
        other = make_affiliate(db, "Other", "other4@test.com")
        make_commission(db, earner=other, amount=Decimal("9.00"))
        db.commit()

        resp = client.get("/api/affiliate/earnings", headers=auth_headers(earner))
        assert resp.json()["earnings"] == []


class TestPayoutRequest:

    def test_payout_rejects_non_positive_amount(self, db, client):
        aff = make_affiliate(db, "Payee", "payee@test.com", total_earnings=Decimal("100"))
        db.commit()

        resp = client.post(
            "/api/affiliate/payout",
            json={"amount": "0", "payment_method": "paypal", "payment_details": "a@b.com"},
            headers=auth_headers(aff),
        )
        assert resp.status_code == 400

    def test_payout_rejects_amount_exceeding_balance(self, db, client):
        aff = make_affiliate(db, "Payee", "payee2@test.com", total_earnings=Decimal("50"))
        db.commit()

        resp = client.post(
            "/api/affiliate/payout",
            json={"amount": "100", "payment_method": "paypal", "payment_details": "a@b.com"},
            headers=auth_headers(aff),
        )
        assert resp.status_code == 400

    def test_payout_subtracts_pending_requests_from_available_balance(self, db, client):
        aff = make_affiliate(db, "Payee", "payee3@test.com", total_earnings=Decimal("100"))
        db.add(PayoutRequest(affiliate_id=aff.id, amount=Decimal("80"), status="pending"))
        db.commit()

        # Only $20 left available; requesting $50 should be rejected.
        resp = client.post(
            "/api/affiliate/payout",
            json={"amount": "50", "payment_method": "paypal", "payment_details": "a@b.com"},
            headers=auth_headers(aff),
        )
        assert resp.status_code == 400

        resp = client.post(
            "/api/affiliate/payout",
            json={"amount": "20", "payment_method": "paypal", "payment_details": "a@b.com"},
            headers=auth_headers(aff),
        )
        assert resp.status_code == 201

    def test_payout_counts_approved_against_balance_but_ignores_rejected(self, db, client):
        """Approved requests represent money already paid out, so they must
        keep counting against future balance forever. Rejected ones never
        happened, so they don't count at all."""
        aff = make_affiliate(db, "Payee", "payee4@test.com", total_earnings=Decimal("100"))
        db.add(PayoutRequest(affiliate_id=aff.id, amount=Decimal("80"), status="approved"))
        db.add(PayoutRequest(affiliate_id=aff.id, amount=Decimal("80"), status="rejected"))
        db.commit()

        # $80 already approved leaves only $20 available; the $80 rejected
        # request doesn't reduce it any further.
        resp = client.post(
            "/api/affiliate/payout",
            json={"amount": "30", "payment_method": "paypal", "payment_details": "a@b.com"},
            headers=auth_headers(aff),
        )
        assert resp.status_code == 400

        resp = client.post(
            "/api/affiliate/payout",
            json={"amount": "20", "payment_method": "paypal", "payment_details": "a@b.com"},
            headers=auth_headers(aff),
        )
        assert resp.status_code == 201

    def test_cannot_request_payout_again_after_prior_one_approved(self, db, client):
        """Regression: approved payouts used to only exclude 'pending'
        requests from the balance check, so once a request was approved it
        stopped counting against the affiliate's balance at all — letting
        them immediately re-request (and re-drain) the same money."""
        aff = make_affiliate(db, "Payee", "payee7@test.com", total_earnings=Decimal("100"))
        admin = make_affiliate(db, "Admin", "admin_payout7@test.com", is_admin=True)
        db.commit()

        first = client.post(
            "/api/affiliate/payout",
            json={"amount": "100", "payment_method": "paypal", "payment_details": "a@b.com"},
            headers=auth_headers(aff),
        )
        assert first.status_code == 201

        approve = client.put(
            f"/api/admin/payouts/{first.json()['id']}",
            json={"status": "approved"},
            headers=auth_headers(admin),
        )
        assert approve.status_code == 200

        second = client.post(
            "/api/affiliate/payout",
            json={"amount": "1", "payment_method": "paypal", "payment_details": "a@b.com"},
            headers=auth_headers(aff),
        )
        assert second.status_code == 400

    def test_successful_payout_created_as_pending(self, db, client):
        aff = make_affiliate(db, "Payee", "payee5@test.com", total_earnings=Decimal("100"))
        db.commit()

        resp = client.post(
            "/api/affiliate/payout",
            json={"amount": "30", "payment_method": "paypal", "payment_details": "a@b.com"},
            headers=auth_headers(aff),
        )
        assert resp.status_code == 201
        assert resp.json()["status"] == "pending"


class TestPayoutsList:

    def test_payouts_only_returns_own_requests(self, db, client):
        aff = make_affiliate(db, "Payee", "payee6@test.com", total_earnings=Decimal("100"))
        other = make_affiliate(db, "Other", "other6@test.com", total_earnings=Decimal("100"))
        db.add(PayoutRequest(affiliate_id=aff.id, amount=Decimal("10"), status="pending"))
        db.add(PayoutRequest(affiliate_id=other.id, amount=Decimal("10"), status="pending"))
        db.commit()

        resp = client.get("/api/affiliate/payouts", headers=auth_headers(aff))
        payouts = resp.json()["payouts"]
        assert len(payouts) == 1
        assert payouts[0]["affiliate_id"] == aff.id
