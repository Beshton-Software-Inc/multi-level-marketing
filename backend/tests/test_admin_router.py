"""Tests for /api/admin (stats, payouts, manual commissions, simulation,
sales team CRUD/membership, commission config, webhook-failure management).
"""
from decimal import Decimal

from app.models import Commission, PayoutRequest, WebhookFailure
from tests.helpers import auth_headers, make_affiliate, make_commission, make_membership, make_team


def _admin(db):
    return make_affiliate(db, "Admin", "admin_router@test.com", is_admin=True)


class TestRequiresAdmin:

    def test_admin_endpoints_reject_non_admin(self, db, client):
        aff = make_affiliate(db, "Regular", "regular_admin@test.com")
        db.commit()
        for path in ("/api/admin/stats", "/api/admin/affiliates", "/api/admin/payouts",
                     "/api/admin/teams", "/api/admin/webhook-failures"):
            resp = client.get(path, headers=auth_headers(aff))
            assert resp.status_code == 403, path


class TestAdminStats:

    def test_stats_only_counts_paid_commissions_and_pending_payouts(self, db, client):
        admin = _admin(db)
        earner = make_affiliate(db, "Earner", "earner_stats@test.com")
        make_commission(db, earner=earner, amount=Decimal("10"), status="paid")
        make_commission(db, earner=earner, amount=Decimal("999"), status="pending")
        db.add(PayoutRequest(affiliate_id=earner.id, amount=Decimal("5"), status="pending"))
        db.add(PayoutRequest(affiliate_id=earner.id, amount=Decimal("777"), status="approved"))
        db.commit()

        resp = client.get("/api/admin/stats", headers=auth_headers(admin))
        body = resp.json()
        assert Decimal(str(body["total_commissions"])) == Decimal("10")
        assert Decimal(str(body["pending_payouts_amount"])) == Decimal("5")
        assert body["pending_payouts_count"] == 1

    def test_stats_affiliate_counts_reflect_status_mix(self, db, client):
        admin = _admin(db)  # active, counts too
        make_affiliate(db, "Active1", "active1_stats@test.com", status="active")
        make_affiliate(db, "Active2", "active2_stats@test.com", status="active")
        make_affiliate(db, "Suspended1", "suspended1_stats@test.com", status="suspended")
        db.commit()

        resp = client.get("/api/admin/stats", headers=auth_headers(admin))
        body = resp.json()
        assert body["total_affiliates"] == 4
        assert body["active_affiliates"] == 3


class TestUpdatePayout:

    def test_unknown_payout_404(self, db, client):
        admin = _admin(db)
        db.commit()
        resp = client.put("/api/admin/payouts/99999", json={"status": "approved"}, headers=auth_headers(admin))
        assert resp.status_code == 404

    def test_approve_marks_commissions_paid_up_to_amount_in_order(self, db, client):
        admin = _admin(db)
        earner = make_affiliate(db, "Earner", "earner_payout@test.com")
        c1 = make_commission(db, earner=earner, amount=Decimal("10"), status="pending")
        c2 = make_commission(db, earner=earner, amount=Decimal("10"), status="pending")
        c3 = make_commission(db, earner=earner, amount=Decimal("10"), status="pending")
        payout = PayoutRequest(affiliate_id=earner.id, amount=Decimal("15"), status="pending")
        db.add(payout)
        db.commit()

        resp = client.put(
            f"/api/admin/payouts/{payout.id}",
            json={"status": "approved"},
            headers=auth_headers(admin),
        )
        assert resp.status_code == 200

        db.refresh(c1)
        db.refresh(c2)
        db.refresh(c3)
        # $15 covers c1 ($10, remaining=$5) then c2 ($10, remaining now negative) -> stop.
        assert c1.status == "paid"
        assert c2.status == "paid"
        assert c3.status == "pending"

    def test_reject_does_not_touch_commissions(self, db, client):
        admin = _admin(db)
        earner = make_affiliate(db, "Earner", "earner_reject@test.com")
        c1 = make_commission(db, earner=earner, amount=Decimal("10"), status="pending")
        payout = PayoutRequest(affiliate_id=earner.id, amount=Decimal("10"), status="pending")
        db.add(payout)
        db.commit()

        resp = client.put(
            f"/api/admin/payouts/{payout.id}",
            json={"status": "rejected"},
            headers=auth_headers(admin),
        )
        assert resp.status_code == 200
        db.refresh(c1)
        assert c1.status == "pending"


class TestManualCommission:

    def test_unknown_affiliate_404(self, db, client):
        admin = _admin(db)
        db.commit()
        resp = client.post(
            "/api/admin/commission",
            json={"affiliate_email": "ghost@test.com", "amount": "10", "description": "bonus"},
            headers=auth_headers(admin),
        )
        assert resp.status_code == 404

    def test_adds_commission_and_updates_total_earnings(self, db, client):
        admin = _admin(db)
        earner = make_affiliate(db, "Earner", "earner_manual@test.com", total_earnings=Decimal("5"))
        db.commit()

        resp = client.post(
            "/api/admin/commission",
            json={"affiliate_email": earner.email, "amount": "10", "description": "bonus"},
            headers=auth_headers(admin),
        )
        assert resp.status_code == 200
        db.refresh(earner)
        assert earner.total_earnings == Decimal("15")


class TestSimulateSubscription:

    def test_unknown_affiliate_404(self, db, client):
        admin = _admin(db)
        db.commit()
        resp = client.post(
            "/api/admin/simulate-subscription",
            json={"affiliate_email": "ghost@test.com", "subscription_amount": "100"},
            headers=auth_headers(admin),
        )
        assert resp.status_code == 404

    def test_no_upline_all_levels_retained_by_platform(self, db, client):
        """With zero ancestors, every one of the 7 levels comes back as a
        'WinWinLaw retains' entry rather than an empty commissions list."""
        admin = _admin(db)
        buyer = make_affiliate(db, "Lonely", "lonely@test.com")
        db.commit()

        resp = client.post(
            "/api/admin/simulate-subscription",
            json={"affiliate_email": buyer.email, "subscription_amount": "100"},
            headers=auth_headers(admin),
        )
        assert resp.status_code == 200
        commissions = resp.json()["commissions"]
        assert len(commissions) == 7
        assert all(c["retained_by_platform"] for c in commissions)

    def test_does_not_persist_commissions(self, db, client):
        admin = _admin(db)
        referrer = make_affiliate(db, "Referrer", "sim_referrer@test.com")
        buyer = make_affiliate(db, "Buyer", "sim_buyer@test.com", referred_by=referrer)
        db.commit()

        resp = client.post(
            "/api/admin/simulate-subscription",
            json={"affiliate_email": buyer.email, "subscription_amount": "100"},
            headers=auth_headers(admin),
        )
        assert resp.status_code == 200
        assert len(resp.json()["commissions"]) > 0
        assert db.query(Commission).count() == 0


class TestSalesTeamCrud:

    def test_create_team_rejects_duplicate_name(self, db, client):
        admin = _admin(db)
        make_team(db, name="Alpha", prefix="ALP")
        db.commit()

        resp = client.post(
            "/api/admin/teams",
            json={"name": "Alpha", "referral_prefix": "OTHER"},
            headers=auth_headers(admin),
        )
        assert resp.status_code == 400

    def test_create_team_rejects_duplicate_prefix(self, db, client):
        admin = _admin(db)
        make_team(db, name="Alpha", prefix="ALP")
        db.commit()

        resp = client.post(
            "/api/admin/teams",
            json={"name": "Different", "referral_prefix": "ALP"},
            headers=auth_headers(admin),
        )
        assert resp.status_code == 400

    def test_get_team_not_found(self, db, client):
        admin = _admin(db)
        db.commit()
        resp = client.get("/api/admin/teams/99999", headers=auth_headers(admin))
        assert resp.status_code == 404

    def test_get_team_includes_members(self, db, client):
        admin = _admin(db)
        team = make_team(db, name="Beta", prefix="BET")
        member = make_affiliate(db, "Member", "member_team@test.com")
        make_membership(db, team, member, role="member")
        db.commit()

        resp = client.get(f"/api/admin/teams/{team.id}", headers=auth_headers(admin))
        assert resp.status_code == 200
        members = resp.json()["members"]
        assert len(members) == 1
        assert members[0]["affiliate_email"] == "member_team@test.com"

    def test_update_team_rejects_rename_to_existing_name(self, db, client):
        admin = _admin(db)
        make_team(db, name="Gamma", prefix="GAM")
        delta = make_team(db, name="Delta", prefix="DEL")
        db.commit()

        resp = client.put(
            f"/api/admin/teams/{delta.id}",
            json={"name": "Gamma"},
            headers=auth_headers(admin),
        )
        assert resp.status_code == 400

    def test_update_team_is_active_toggle_round_trips(self, db, client):
        admin = _admin(db)
        team = make_team(db, name="Kappa", prefix="KAP")
        db.commit()
        assert team.is_active is True

        resp = client.put(
            f"/api/admin/teams/{team.id}",
            json={"is_active": False},
            headers=auth_headers(admin),
        )
        assert resp.status_code == 200
        assert resp.json()["is_active"] is False

        resp = client.put(
            f"/api/admin/teams/{team.id}",
            json={"is_active": True},
            headers=auth_headers(admin),
        )
        assert resp.status_code == 200
        assert resp.json()["is_active"] is True

    def test_create_team_rejects_commission_rate_above_100(self, db, client):
        admin = _admin(db)
        db.commit()
        resp = client.post(
            "/api/admin/teams",
            json={"name": "Overflow", "referral_prefix": "OVF", "commission_rate": "150"},
            headers=auth_headers(admin),
        )
        assert resp.status_code == 422

    def test_create_team_rejects_negative_commission_rate(self, db, client):
        admin = _admin(db)
        db.commit()
        resp = client.post(
            "/api/admin/teams",
            json={"name": "Negative", "referral_prefix": "NEG", "commission_rate": "-1"},
            headers=auth_headers(admin),
        )
        assert resp.status_code == 422

    def test_update_team_rejects_commission_rate_out_of_range(self, db, client):
        admin = _admin(db)
        team = make_team(db, name="Lambda", prefix="LAM")
        db.commit()
        resp = client.put(
            f"/api/admin/teams/{team.id}",
            json={"commission_rate": "101"},
            headers=auth_headers(admin),
        )
        assert resp.status_code == 422


class TestTeamMembership:

    def test_add_member_unknown_team_404(self, db, client):
        admin = _admin(db)
        aff = make_affiliate(db, "Aff", "aff_add@test.com")
        db.commit()
        resp = client.post(
            "/api/admin/teams/99999/members",
            json={"affiliate_email": aff.email},
            headers=auth_headers(admin),
        )
        assert resp.status_code == 404

    def test_add_member_unknown_affiliate_404(self, db, client):
        admin = _admin(db)
        team = make_team(db, name="Epsilon", prefix="EPS")
        db.commit()
        resp = client.post(
            f"/api/admin/teams/{team.id}/members",
            json={"affiliate_email": "ghost@test.com"},
            headers=auth_headers(admin),
        )
        assert resp.status_code == 404

    def test_add_member_already_on_another_team_rejected(self, db, client):
        admin = _admin(db)
        team_a = make_team(db, name="Zeta", prefix="ZET")
        team_b = make_team(db, name="Eta", prefix="ETA")
        aff = make_affiliate(db, "Busy", "busy@test.com")
        make_membership(db, team_a, aff)
        db.commit()

        resp = client.post(
            f"/api/admin/teams/{team_b.id}/members",
            json={"affiliate_email": aff.email},
            headers=auth_headers(admin),
        )
        assert resp.status_code == 400

    def test_update_role_and_remove_member(self, db, client):
        admin = _admin(db)
        team = make_team(db, name="Theta", prefix="THE")
        aff = make_affiliate(db, "Member", "member_role@test.com")
        make_membership(db, team, aff, role="member")
        db.commit()

        resp = client.put(
            f"/api/admin/teams/{team.id}/members/{aff.id}",
            json={"role": "admin"},
            headers=auth_headers(admin),
        )
        assert resp.status_code == 200

        resp = client.delete(f"/api/admin/teams/{team.id}/members/{aff.id}", headers=auth_headers(admin))
        assert resp.status_code == 200

        resp = client.get(f"/api/admin/teams/{team.id}", headers=auth_headers(admin))
        assert resp.json()["members"] == []


class TestCommissionConfig:

    def test_partial_update_leaves_unset_fields_unchanged(self, db, client):
        admin = _admin(db)
        team = make_team(db, name="Iota", prefix="IOT", commission_mode="custom", custom_rate_l1=20)
        db.commit()

        resp = client.put(
            f"/api/admin/teams/{team.id}/commission-config",
            json={"custom_rate_l2": 5},
            headers=auth_headers(admin),
        )
        assert resp.status_code == 200
        body = resp.json()
        assert Decimal(str(body["custom_rate_l1"])) == Decimal("20")
        assert Decimal(str(body["custom_rate_l2"])) == Decimal("5")
        assert body["commission_mode"] == "custom"

    def test_get_config_not_found(self, db, client):
        admin = _admin(db)
        db.commit()
        resp = client.get("/api/admin/teams/99999/commission-config", headers=auth_headers(admin))
        assert resp.status_code == 404

    def test_update_rejects_custom_rate_out_of_range(self, db, client):
        admin = _admin(db)
        team = make_team(db, name="Mu", prefix="MU1")
        db.commit()
        resp = client.put(
            f"/api/admin/teams/{team.id}/commission-config",
            json={"custom_rate_l1": "150"},
            headers=auth_headers(admin),
        )
        assert resp.status_code == 422

    def test_update_rejects_negative_custom_rate(self, db, client):
        admin = _admin(db)
        team = make_team(db, name="Nu", prefix="NU1")
        db.commit()
        resp = client.put(
            f"/api/admin/teams/{team.id}/commission-config",
            json={"custom_rate_l1": "-5"},
            headers=auth_headers(admin),
        )
        assert resp.status_code == 422


class TestWebhookFailures:

    def test_list_filters_by_resolved(self, db, client):
        admin = _admin(db)
        db.add(WebhookFailure(
            subscription_id="sub1", referral_code="AAA", customer_email="a@test.com",
            payload="{}", error_message="boom", resolved=False,
        ))
        db.add(WebhookFailure(
            subscription_id="sub2", referral_code="BBB", customer_email="b@test.com",
            payload="{}", error_message="boom", resolved=True,
        ))
        db.commit()

        resp = client.get("/api/admin/webhook-failures?resolved=false", headers=auth_headers(admin))
        failures = resp.json()["failures"]
        assert len(failures) == 1
        assert failures[0]["subscription_id"] == "sub1"

    def test_resolve_unknown_404(self, db, client):
        admin = _admin(db)
        db.commit()
        resp = client.post("/api/admin/webhook-failures/99999/resolve", headers=auth_headers(admin))
        assert resp.status_code == 404

    def test_resolve_is_idempotent(self, db, client):
        admin = _admin(db)
        failure = WebhookFailure(
            subscription_id="sub3", referral_code="CCC", customer_email="c@test.com",
            payload="{}", error_message="boom", resolved=False,
        )
        db.add(failure)
        db.commit()

        resp1 = client.post(f"/api/admin/webhook-failures/{failure.id}/resolve", headers=auth_headers(admin))
        assert resp1.status_code == 200
        assert resp1.json()["message"] == "Marked as resolved"

        resp2 = client.post(f"/api/admin/webhook-failures/{failure.id}/resolve", headers=auth_headers(admin))
        assert resp2.status_code == 200
        assert resp2.json()["message"] == "Already resolved"


class TestListEndpoints:

    def test_list_affiliates_returns_all(self, db, client):
        admin = _admin(db)
        make_affiliate(db, "Listed1", "listed1@test.com")
        make_affiliate(db, "Listed2", "listed2@test.com")
        db.commit()

        resp = client.get("/api/admin/affiliates", headers=auth_headers(admin))
        assert resp.status_code == 200
        emails = {a["email"] for a in resp.json()["affiliates"]}
        assert {"listed1@test.com", "listed2@test.com", admin.email} <= emails

    def test_list_payouts_includes_joined_affiliate_fields(self, db, client):
        admin = _admin(db)
        earner = make_affiliate(db, "PayoutOwner", "payout_owner@test.com")
        db.add(PayoutRequest(affiliate_id=earner.id, amount=Decimal("25"), status="pending"))
        db.commit()

        resp = client.get("/api/admin/payouts", headers=auth_headers(admin))
        assert resp.status_code == 200
        payouts = resp.json()["payouts"]
        assert len(payouts) == 1
        assert payouts[0]["affiliate_name"] == "PayoutOwner"
        assert payouts[0]["affiliate_email"] == "payout_owner@test.com"

    def test_list_teams_returns_member_counts(self, db, client):
        admin = _admin(db)
        team = make_team(db, name="Xi", prefix="XI1")
        member = make_affiliate(db, "Member", "member_xi@test.com")
        make_membership(db, team, member)
        db.commit()

        resp = client.get("/api/admin/teams", headers=auth_headers(admin))
        assert resp.status_code == 200
        teams = {t["name"]: t for t in resp.json()["teams"]}
        assert teams["Xi"]["member_count"] == 1
