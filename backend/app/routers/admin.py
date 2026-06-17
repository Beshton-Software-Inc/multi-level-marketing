from datetime import datetime, timezone
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Affiliate, Commission, PayoutRequest
from app.schemas.admin import (
    AdminStats,
    PayoutUpdateRequest,
    ManualCommissionRequest,
    SimulateSubscriptionRequest,
    SimulatedCommission,
)
from app.schemas.affiliate import AffiliateResponse, PayoutRequestResponse
from app.services.auth_service import require_admin
from app.services.mlm_service import preview_commission_breakdown

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.get("/stats", response_model=AdminStats)
def admin_stats(admin: Affiliate = Depends(require_admin), db: Session = Depends(get_db)):
    total_affiliates = db.query(Affiliate).count()
    active_affiliates = db.query(Affiliate).filter(Affiliate.status == "active").count()

    total_commissions = db.query(func.coalesce(func.sum(Commission.amount), 0)).filter(
        Commission.status == "paid"
    ).scalar() or Decimal("0")

    pending_payouts_amount = db.query(func.coalesce(func.sum(PayoutRequest.amount), 0)).filter(
        PayoutRequest.status == "pending"
    ).scalar() or Decimal("0")

    pending_payouts_count = db.query(PayoutRequest).filter(PayoutRequest.status == "pending").count()

    return AdminStats(
        total_affiliates=total_affiliates,
        active_affiliates=active_affiliates,
        total_commissions=Decimal(str(total_commissions)),
        pending_payouts_amount=Decimal(str(pending_payouts_amount)),
        pending_payouts_count=pending_payouts_count,
    )


@router.get("/affiliates")
def list_affiliates(admin: Affiliate = Depends(require_admin), db: Session = Depends(get_db)):
    affiliates = db.query(Affiliate).order_by(Affiliate.created_at.desc()).all()
    return {"affiliates": [AffiliateResponse.model_validate(a) for a in affiliates]}


@router.get("/payouts")
def list_payouts(admin: Affiliate = Depends(require_admin), db: Session = Depends(get_db)):
    payouts = db.query(PayoutRequest).order_by(PayoutRequest.created_at.desc()).all()
    result = []
    for p in payouts:
        data = PayoutRequestResponse.model_validate(p)
        data_dict = data.model_dump()
        data_dict["affiliate_name"] = p.affiliate.name if p.affiliate else None
        data_dict["affiliate_email"] = p.affiliate.email if p.affiliate else None
        result.append(data_dict)
    return {"payouts": result}


@router.put("/payouts/{payout_id}")
def update_payout(
    payout_id: int,
    body: PayoutUpdateRequest,
    admin: Affiliate = Depends(require_admin),
    db: Session = Depends(get_db),
):
    payout = db.query(PayoutRequest).filter(PayoutRequest.id == payout_id).first()
    if not payout:
        raise HTTPException(status_code=404, detail="Payout request not found")

    payout.status = body.status
    payout.admin_notes = body.admin_notes
    payout.processed_at = datetime.now(timezone.utc)

    # If approved, mark related commissions as paid up to this amount
    if body.status == "approved":
        pending_commissions = (
            db.query(Commission)
            .filter(Commission.earner_id == payout.affiliate_id, Commission.status == "pending")
            .order_by(Commission.created_at)
            .all()
        )
        remaining = payout.amount
        for c in pending_commissions:
            if remaining <= 0:
                break
            c.status = "paid"
            remaining -= c.amount

    db.commit()
    db.refresh(payout)
    return PayoutRequestResponse.model_validate(payout)


@router.post("/commission")
def add_commission(
    body: ManualCommissionRequest,
    admin: Affiliate = Depends(require_admin),
    db: Session = Depends(get_db),
):
    affiliate = db.query(Affiliate).filter(Affiliate.email == body.affiliate_email).first()
    if not affiliate:
        raise HTTPException(status_code=404, detail="Affiliate not found")

    amount = body.amount
    commission = Commission(
        earner_id=affiliate.id,
        source_id=None,
        amount=amount,
        tier=1,
        description=body.description,
        status="pending",
    )
    db.add(commission)
    affiliate.total_earnings = (affiliate.total_earnings or Decimal("0")) + amount
    db.commit()
    db.refresh(commission)
    return {"message": "Commission added", "commission_id": commission.id, "amount": float(amount)}


@router.post("/simulate-subscription")
def simulate_subscription(
    body: SimulateSubscriptionRequest,
    admin: Affiliate = Depends(require_admin),
    db: Session = Depends(get_db),
):
    affiliate = db.query(Affiliate).filter(Affiliate.email == body.affiliate_email).first()
    if not affiliate:
        raise HTTPException(status_code=404, detail="Affiliate not found")

    breakdown = preview_commission_breakdown(affiliate.id, body.subscription_amount, db)
    commissions = [SimulatedCommission.model_validate(c) for c in breakdown]

    if not commissions:
        return {
            "message": f"No upline found for {affiliate.name} — no commissions would be earned.",
            "buyer_name": affiliate.name,
            "buyer_email": affiliate.email,
            "subscription_amount": body.subscription_amount,
            "commissions": [],
        }

    return {
        "message": f"Estimated commissions for a ${body.subscription_amount} subscription by {affiliate.name} (not saved)",
        "buyer_name": affiliate.name,
        "buyer_email": affiliate.email,
        "subscription_amount": body.subscription_amount,
        "commissions": commissions,
    }
