from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Affiliate, Commission, PayoutRequest
from app.schemas.affiliate import (
    AffiliateResponse, AffiliateStats, CommissionResponse,
    PayoutRequestCreate, PayoutRequestResponse, TeamMember
)
from app.services.auth_service import get_current_affiliate
from app.services.mlm_service import get_team_members, get_affiliate_stats

router = APIRouter(prefix="/api/affiliate", tags=["affiliate"])


@router.get("/me", response_model=AffiliateResponse)
def get_me(current: Affiliate = Depends(get_current_affiliate)):
    return current


@router.get("/stats", response_model=AffiliateStats)
def get_stats(current: Affiliate = Depends(get_current_affiliate), db: Session = Depends(get_db)):
    stats = get_affiliate_stats(current.id, db)
    return AffiliateStats(**stats)


@router.get("/team")
def get_team(current: Affiliate = Depends(get_current_affiliate), db: Session = Depends(get_db)):
    members = get_team_members(current.id, db)
    return {"members": members}


@router.get("/earnings")
def get_earnings(
    skip: int = 0,
    limit: int = 50,
    current: Affiliate = Depends(get_current_affiliate),
    db: Session = Depends(get_db),
):
    commissions = (
        db.query(Commission)
        .filter(Commission.earner_id == current.id)
        .order_by(Commission.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    result = []
    for c in commissions:
        source_name = None
        if c.source_id:
            src = db.query(Affiliate).filter(Affiliate.id == c.source_id).first()
            source_name = src.name if src else None

        result.append(CommissionResponse(
            id=c.id,
            earner_id=c.earner_id,
            source_id=c.source_id,
            source_name=source_name,
            amount=c.amount,
            tier=c.tier,
            description=c.description,
            status=c.status,
            created_at=c.created_at,
        ))

    return {"earnings": result}


@router.post("/payout", response_model=PayoutRequestResponse, status_code=status.HTTP_201_CREATED)
def request_payout(
    body: PayoutRequestCreate,
    current: Affiliate = Depends(get_current_affiliate),
    db: Session = Depends(get_db),
):
    if body.amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be positive")

    # Check available balance: total_earnings - already pending requests
    from sqlalchemy import func as sqlfunc
    pending_total = db.query(sqlfunc.coalesce(sqlfunc.sum(PayoutRequest.amount), 0)).filter(
        PayoutRequest.affiliate_id == current.id,
        PayoutRequest.status == "pending",
    ).scalar() or Decimal("0")

    available = (current.total_earnings or Decimal("0")) - Decimal(str(pending_total))
    if body.amount > available:
        raise HTTPException(
            status_code=400,
            detail=f"Requested amount exceeds available balance ${available:.2f}"
        )

    payout = PayoutRequest(
        affiliate_id=current.id,
        amount=body.amount,
        payment_method=body.payment_method,
        payment_details=body.payment_details,
    )
    db.add(payout)
    db.commit()
    db.refresh(payout)
    return payout


@router.get("/payouts")
def get_payouts(current: Affiliate = Depends(get_current_affiliate), db: Session = Depends(get_db)):
    payouts = (
        db.query(PayoutRequest)
        .filter(PayoutRequest.affiliate_id == current.id)
        .order_by(PayoutRequest.created_at.desc())
        .all()
    )
    return {"payouts": [PayoutRequestResponse.model_validate(p) for p in payouts]}
