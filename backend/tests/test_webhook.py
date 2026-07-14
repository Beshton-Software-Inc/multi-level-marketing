"""Tests for /api/webhook/subscription.

Covers secret verification, unknown/suspended/no-team/team-with-policy
referral resolution, failure logging, and — the fix for the bug where a
retried delivery would pay the same subscription's commission cascade
twice — duplicate subscription_id detection.
"""
from decimal import Decimal

from app.config import settings
from app.models import Commission, WebhookFailure
from tests.helpers import make_affiliate, make_membership, make_team


def _payload(**overrides):
    body = {
        "referral_code": "WWL00000",
        "customer_email": "customer@test.com",
        "customer_name": "Customer",
        "plan_name": "Professional Gold",
        "amount": 100.0,
        "subscription_id": "sub_1",
    }
    body.update(overrides)
    return body


def _post(client, payload, secret=None):
    headers = {"X-Webhook-Secret": secret if secret is not None else settings.MLM_WEBHOOK_SECRET}
    return client.post("/api/webhook/subscription", json=payload, headers=headers)


class TestAuth:

    def test_missing_secret_rejected(self, db, client):
        resp = client.post("/api/webhook/subscription", json=_payload())
        assert resp.status_code == 401

    def test_wrong_secret_rejected(self, db, client):
        resp = _post(client, _payload(), secret="wrong-secret")
        assert resp.status_code == 401


class TestReferralResolution:

    def test_unknown_referral_code_is_non_fatal_skip(self, db, client):
        resp = _post(client, _payload(referral_code="NOPE0000"))
        assert resp.status_code == 200
        assert resp.json()["status"] == "skipped"

    def test_suspended_affiliate_is_skipped(self, db, client):
        aff = make_affiliate(db, "Suspended", "susp_wh@test.com", status="suspended")
        db.commit()

        resp = _post(client, _payload(referral_code=aff.referral_code))
        assert resp.status_code == 200
        assert resp.json()["status"] == "skipped"
        assert db.query(Commission).count() == 0

    def test_no_team_uses_100pct_platform_default_rates(self, db, client):
        referrer = make_affiliate(db, "Referrer", "referrer_wh@test.com")
        buyer = make_affiliate(db, "Buyer", "buyer_wh@test.com", referred_by=referrer)
        db.commit()

        resp = _post(client, _payload(referral_code=buyer.referral_code, amount=100.0))
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "ok"
        assert body["team_commission_rate"] == 100.0

        commission = db.query(Commission).filter(Commission.earner_id == referrer.id).first()
        # L1 default rate is 20% of a $100 sub at 100% team allocation = $20.
        assert commission.amount == Decimal("20.00")

    def test_active_team_uses_team_rate_and_custom_policy(self, db, client):
        referrer = make_affiliate(db, "Referrer", "referrer_team@test.com")
        buyer = make_affiliate(db, "Buyer", "buyer_team@test.com", referred_by=referrer)
        team = make_team(db, name="WH Team", prefix="WHT", commission_rate=50,
                          commission_mode="custom", custom_rate_l1=10)
        make_membership(db, team, buyer)
        db.commit()

        resp = _post(client, _payload(referral_code=buyer.referral_code, amount=100.0))
        assert resp.status_code == 200
        body = resp.json()
        assert body["team_commission_rate"] == 50.0
        assert body["team_name"] == "WH Team"

        commission = db.query(Commission).filter(Commission.earner_id == referrer.id).first()
        # team_share = 100 * 50% = 50; L1 custom rate 10% of 50 = $5.
        assert commission.amount == Decimal("5.00")

    def test_inactive_team_falls_back_to_no_team_defaults(self, db, client):
        referrer = make_affiliate(db, "Referrer", "referrer_inactive@test.com")
        buyer = make_affiliate(db, "Buyer", "buyer_inactive@test.com", referred_by=referrer)
        team = make_team(db, name="Inactive Team", prefix="INT", commission_rate=10)
        team.is_active = False
        make_membership(db, team, buyer)
        db.commit()

        resp = _post(client, _payload(referral_code=buyer.referral_code, amount=100.0))
        assert resp.json()["team_commission_rate"] == 100.0

    def test_retain_admin_policy_resolves_team_admin(self, db, client):
        referrer = make_affiliate(db, "Referrer", "referrer_ra@test.com")  # fills L1 naturally
        buyer = make_affiliate(db, "Buyer", "buyer_ra@test.com", referred_by=referrer)
        admin_aff = make_affiliate(db, "TeamAdmin", "teamadmin_wh@test.com")
        team = make_team(db, name="RA Team", prefix="RAT", commission_rate=100,
                          unassigned_policy="retain_admin")
        make_membership(db, team, admin_aff, role="admin")
        make_membership(db, team, buyer, role="member")
        db.commit()

        resp = _post(client, _payload(referral_code=buyer.referral_code, amount=100.0))
        assert resp.status_code == 200

        # L1 goes to referrer naturally; L2-L7 have no natural earner and roll
        # up to the team admin under retain_admin.
        assert db.query(Commission).filter(Commission.earner_id == referrer.id).count() == 1
        assert db.query(Commission).filter(Commission.earner_id == admin_aff.id).count() == 6


class TestFailureLogging:

    def test_cascade_exception_logs_webhook_failure_and_returns_500(self, db, client, monkeypatch):
        referrer = make_affiliate(db, "Referrer", "referrer_fail@test.com")
        buyer = make_affiliate(db, "Buyer", "buyer_fail@test.com", referred_by=referrer)
        db.commit()

        def boom(*args, **kwargs):
            raise RuntimeError("simulated cascade failure")

        monkeypatch.setattr("app.routers.webhook.calculate_and_create_commissions", boom)

        resp = _post(client, _payload(referral_code=buyer.referral_code, subscription_id="sub_boom"))
        assert resp.status_code == 500

        failure = db.query(WebhookFailure).filter(WebhookFailure.subscription_id == "sub_boom").first()
        assert failure is not None
        assert failure.referral_code == buyer.referral_code
        assert failure.resolved is False
        assert "simulated cascade failure" in failure.error_message


class TestDuplicateDeliveryIdempotency:
    """Regression coverage for the fix: a retried webhook delivery for a
    subscription_id that's already been processed must not pay out a second
    round of commissions."""

    def test_first_delivery_processes_normally(self, db, client):
        referrer = make_affiliate(db, "Referrer", "referrer_dup1@test.com")
        buyer = make_affiliate(db, "Buyer", "buyer_dup1@test.com", referred_by=referrer)
        db.commit()

        resp = _post(client, _payload(referral_code=buyer.referral_code, subscription_id="sub_dup_1"))
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"
        assert db.query(Commission).filter(Commission.earner_id == referrer.id).count() == 7

    def test_duplicate_delivery_is_a_noop(self, db, client):
        referrer = make_affiliate(db, "Referrer", "referrer_dup2@test.com")
        buyer = make_affiliate(db, "Buyer", "buyer_dup2@test.com", referred_by=referrer)
        db.commit()

        first = _post(client, _payload(referral_code=buyer.referral_code, subscription_id="sub_dup_2"))
        assert first.status_code == 200
        assert first.json()["status"] == "ok"

        db.refresh(referrer)
        earnings_after_first = referrer.total_earnings
        commission_count_after_first = db.query(Commission).count()

        second = _post(client, _payload(referral_code=buyer.referral_code, subscription_id="sub_dup_2"))
        assert second.status_code == 200
        assert second.json()["status"] == "duplicate"

        db.refresh(referrer)
        assert referrer.total_earnings == earnings_after_first
        assert db.query(Commission).count() == commission_count_after_first

    def test_different_subscription_ids_both_process(self, db, client):
        """Sanity check that the dup-check is keyed on subscription_id, not
        just the referral_code — the same affiliate can generate two
        separate subscriptions."""
        referrer = make_affiliate(db, "Referrer", "referrer_dup3@test.com")
        buyer = make_affiliate(db, "Buyer", "buyer_dup3@test.com", referred_by=referrer)
        db.commit()

        first = _post(client, _payload(referral_code=buyer.referral_code, subscription_id="sub_dup_3a"))
        second = _post(client, _payload(referral_code=buyer.referral_code, subscription_id="sub_dup_3b"))
        assert first.json()["status"] == "ok"
        assert second.json()["status"] == "ok"
        assert db.query(Commission).filter(Commission.earner_id == referrer.id).count() == 14
