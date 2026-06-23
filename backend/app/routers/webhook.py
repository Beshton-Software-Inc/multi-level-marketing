"""
Server-to-server webhook called by the winwinlaw backend after a successful
subscription. Authenticates via a shared secret header, then fires the MLM
commission cascade for the referring affiliate.
"""
from decimal import Decimal

from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional

from app.config import settings
from app.database import get_db
from app.models import Affiliate, TeamMembership
from app.services.mlm_service import build_effective_rates, calculate_and_create_commissions

router = APIRouter(prefix="/api/webhook", tags=["webhook"])


class SubscriptionWebhookPayload(BaseModel):
    referral_code: str        # 8-char affiliate code (e.g. "WWL1A2B3")
    customer_email: str
    customer_name: str
    plan_name: str            # e.g. "Professional Gold"
    amount: float             # Subscription amount in dollars (e.g. 299.00)
    subscription_id: str      # Winwinlaw subscription_id for idempotency


def _verify_secret(x_webhook_secret: Optional[str] = Header(default=None)):
    if x_webhook_secret != settings.MLM_WEBHOOK_SECRET:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid webhook secret")


@router.post("/subscription", status_code=status.HTTP_200_OK)
def subscription_webhook(
    payload: SubscriptionWebhookPayload,
    db: Session = Depends(get_db),
    _: None = Depends(_verify_secret),
):
    """
    Called by winwinlaw backend when a subscriber completes payment with a
    WWL-prefixed referral code. Finds the affiliate and distributes commissions
    up the MLM tree (L1=20%, L2=10%, L3=5%).
    """
    affiliate = db.query(Affiliate).filter(
        Affiliate.referral_code == payload.referral_code.upper()
    ).first()

    if not affiliate:
        # Non-fatal: the code might have been mis-entered; log but don't error
        # so the caller's subscription flow isn't blocked.
        return {
            "status": "skipped",
            "reason": f"referral_code '{payload.referral_code}' not found in MLM",
        }

    if affiliate.status != "active":
        return {
            "status": "skipped",
            "reason": f"affiliate '{payload.referral_code}' is not active",
        }

    # Look up this affiliate's team to get commission config.
    # If no team, default to 100% with platform rates.
    team_commission_rate = Decimal("100")
    team_name = None
    commission_rates = None
    unassigned_policy = "compress"
    team_admin_id = None

    membership = db.query(TeamMembership).filter(
        TeamMembership.affiliate_id == affiliate.id
    ).first()
    if membership and membership.team and membership.team.is_active:
        team = membership.team
        team_commission_rate = Decimal(str(team.commission_rate))
        team_name = team.name
        commission_rates = build_effective_rates(team)
        unassigned_policy = team.unassigned_policy or "compress"
        if unassigned_policy == "retain_admin":
            admin_membership = db.query(TeamMembership).filter(
                TeamMembership.team_id == team.id,
                TeamMembership.role == "admin",
            ).first()
            if admin_membership:
                team_admin_id = admin_membership.affiliate_id

    calculate_and_create_commissions(
        new_affiliate_id=affiliate.id,
        subscription_amount=Decimal(str(payload.amount)),
        db=db,
        team_commission_rate=team_commission_rate,
        commission_rates=commission_rates,
        unassigned_policy=unassigned_policy,
        team_admin_id=team_admin_id,
    )

    return {
        "status": "ok",
        "affiliate_id": affiliate.id,
        "affiliate_name": affiliate.name,
        "subscription_id": payload.subscription_id,
        "amount": payload.amount,
        "team_name": team_name,
        "team_commission_rate": float(team_commission_rate),
    }
