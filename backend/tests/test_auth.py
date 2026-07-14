"""Tests for /api/auth (register, login) and the auth_service primitives
that back token issuance and route protection.
"""
from datetime import timedelta

import pytest
from jose import jwt

from app.config import settings
from app.services.auth_service import (
    ALGORITHM,
    create_access_token,
    generate_referral_code,
    hash_password,
    verify_password,
)
from tests.helpers import make_affiliate


class TestRegister:

    def test_register_creates_affiliate_and_returns_token(self, client, db):
        resp = client.post("/api/auth/register", json={
            "name": "Alice",
            "email": "alice@test.com",
            "password": "hunter2",
        })
        assert resp.status_code == 201
        body = resp.json()
        assert body["user"]["email"] == "alice@test.com"
        assert body["user"]["referral_code"]
        assert len(body["user"]["referral_code"]) == 8
        assert body["access_token"]

        # Token is valid and points at the new affiliate.
        payload = jwt.decode(body["access_token"], settings.SECRET_KEY, algorithms=[ALGORITHM])
        assert int(payload["sub"]) == body["user"]["id"]

    def test_register_duplicate_email_rejected(self, client, db):
        make_affiliate(db, "Existing", "dupe@test.com")
        db.commit()

        resp = client.post("/api/auth/register", json={
            "name": "New Person",
            "email": "dupe@test.com",
            "password": "hunter2",
        })
        assert resp.status_code == 400

    def test_register_with_valid_referral_code_links_referrer(self, client, db):
        referrer = make_affiliate(db, "Referrer", "referrer@test.com")
        db.commit()

        resp = client.post("/api/auth/register", json={
            "name": "Referred",
            "email": "referred@test.com",
            "password": "hunter2",
            "referral_code": referrer.referral_code,
        })
        assert resp.status_code == 201
        new_id = resp.json()["user"]["id"]

        from app.models import Affiliate
        new_aff = db.query(Affiliate).filter(Affiliate.id == new_id).first()
        assert new_aff.referred_by_id == referrer.id

    def test_register_with_unknown_referral_code_rejected(self, client, db):
        resp = client.post("/api/auth/register", json={
            "name": "New Person",
            "email": "new@test.com",
            "password": "hunter2",
            "referral_code": "NOSUCHCODE",
        })
        assert resp.status_code == 400

    def test_register_generates_unique_referral_codes(self, client, db, monkeypatch):
        """First call to generate_referral_code collides; register should retry."""
        existing = make_affiliate(db, "Taken", "taken@test.com")
        db.commit()
        taken_code = existing.referral_code

        calls = {"n": 0}
        real_generate = generate_referral_code

        def flaky_generate():
            calls["n"] += 1
            return taken_code if calls["n"] == 1 else real_generate()

        monkeypatch.setattr("app.routers.auth.generate_referral_code", flaky_generate)

        resp = client.post("/api/auth/register", json={
            "name": "New Person",
            "email": "new2@test.com",
            "password": "hunter2",
        })
        assert resp.status_code == 201
        assert resp.json()["user"]["referral_code"] != taken_code
        assert calls["n"] >= 2


class TestLogin:

    def test_login_success_returns_token(self, client, db):
        make_affiliate(db, "Bob", "bob@test.com", password="correcthorse")
        db.commit()

        resp = client.post("/api/auth/login", json={
            "email": "bob@test.com",
            "password": "correcthorse",
        })
        assert resp.status_code == 200
        assert resp.json()["access_token"]

    def test_login_wrong_password_rejected(self, client, db):
        make_affiliate(db, "Bob", "bob@test.com", password="correcthorse")
        db.commit()

        resp = client.post("/api/auth/login", json={
            "email": "bob@test.com",
            "password": "wrongpassword",
        })
        assert resp.status_code == 401

    def test_login_unknown_email_rejected(self, client, db):
        resp = client.post("/api/auth/login", json={
            "email": "ghost@test.com",
            "password": "whatever",
        })
        assert resp.status_code == 401

    def test_login_suspended_account_rejected(self, client, db):
        make_affiliate(db, "Suspended", "suspended@test.com", password="pw", status="suspended")
        db.commit()

        resp = client.post("/api/auth/login", json={
            "email": "suspended@test.com",
            "password": "pw",
        })
        assert resp.status_code == 403


class TestAuthServicePrimitives:

    def test_hash_and_verify_password_round_trip(self):
        hashed = hash_password("s3cret!")
        assert hashed != "s3cret!"
        assert verify_password("s3cret!", hashed)
        assert not verify_password("wrong", hashed)

    def test_generate_referral_code_format(self):
        code = generate_referral_code()
        assert len(code) == 8
        assert all(c.isupper() or c.isdigit() for c in code)

    def test_expired_token_rejected(self, client, db):
        aff = make_affiliate(db, "Expiring", "expiring@test.com")
        db.commit()
        token = create_access_token({"sub": str(aff.id)}, expires_delta=timedelta(minutes=-1))

        resp = client.get("/api/affiliate/me", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 401

    def test_malformed_token_rejected(self, client, db):
        resp = client.get("/api/affiliate/me", headers={"Authorization": "Bearer not-a-real-token"})
        assert resp.status_code == 401

    def test_missing_token_rejected(self, client, db):
        resp = client.get("/api/affiliate/me")
        assert resp.status_code in (401, 403)

    def test_token_for_deleted_affiliate_rejected(self, client, db):
        token = create_access_token({"sub": "999999"})
        resp = client.get("/api/affiliate/me", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 401

    def test_token_for_suspended_affiliate_forbidden(self, client, db):
        aff = make_affiliate(db, "Suspended", "susp2@test.com", status="suspended")
        db.commit()
        token = create_access_token({"sub": str(aff.id)})

        resp = client.get("/api/affiliate/me", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 403

    def test_require_admin_rejects_non_admin(self, client, db):
        from tests.helpers import auth_headers
        aff = make_affiliate(db, "Regular", "regular@test.com", is_admin=False)
        db.commit()

        resp = client.get("/api/admin/stats", headers=auth_headers(aff))
        assert resp.status_code == 403

    def test_require_admin_allows_admin(self, client, db):
        from tests.helpers import auth_headers
        aff = make_affiliate(db, "Admin", "admin@test.com", is_admin=True)
        db.commit()

        resp = client.get("/api/admin/stats", headers=auth_headers(aff))
        assert resp.status_code == 200
