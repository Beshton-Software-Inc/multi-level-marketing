from decimal import Decimal
from datetime import datetime, timezone
from typing import List, Dict, Any

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import Affiliate, Commission


# Commission rates by level
COMMISSION_RATES = {1: Decimal("0.20"), 2: Decimal("0.10"), 3: Decimal("0.05")}
MAX_LEVELS = 3


def get_team_members(affiliate_id: int, db: Session) -> List[Dict[str, Any]]:
    """Recursively get all downline members with their depth."""
    result = []
    visited = set()

    def recurse(parent_id: int, depth: int):
        if depth > 10:
            return
        children = db.query(Affiliate).filter(Affiliate.referred_by_id == parent_id).all()
        for child in children:
            if child.id in visited:
                continue
            visited.add(child.id)
            direct_refs = db.query(Affiliate).filter(Affiliate.referred_by_id == child.id).count()
            result.append({
                "id": child.id,
                "name": child.name,
                "email": child.email,
                "referral_code": child.referral_code,
                "status": child.status,
                "total_earnings": child.total_earnings,
                "created_at": child.created_at,
                "depth": depth,
                "direct_referrals": direct_refs,
            })
            recurse(child.id, depth + 1)

    recurse(affiliate_id, 1)
    return result


def preview_commission_breakdown(
    buyer_affiliate_id: int,
    subscription_amount: Decimal,
    db: Session,
) -> List[Dict[str, Any]]:
    """Walk up the referral tree and return estimated commissions without persisting."""
    affiliate = db.query(Affiliate).filter(Affiliate.id == buyer_affiliate_id).first()
    if not affiliate:
        return []

    breakdown: List[Dict[str, Any]] = []
    current = affiliate
    for level in range(1, MAX_LEVELS + 1):
        if current.referred_by_id is None:
            break
        referrer = db.query(Affiliate).filter(Affiliate.id == current.referred_by_id).first()
        if not referrer:
            break

        rate = COMMISSION_RATES[level]
        amount = (subscription_amount * rate).quantize(Decimal("0.01"))
        breakdown.append({
            "earner_name": referrer.name,
            "earner_email": referrer.email,
            "tier": level,
            "amount": amount,
        })
        current = referrer

    return breakdown


def calculate_and_create_commissions(new_affiliate_id: int, subscription_amount: Decimal, db: Session) -> List[Dict[str, Any]]:
    """Walk up the referral tree and create commission records for up to 3 levels."""
    affiliate = db.query(Affiliate).filter(Affiliate.id == new_affiliate_id).first()
    if not affiliate:
        return []

    created: List[Dict[str, Any]] = []
    current = affiliate
    for level in range(1, MAX_LEVELS + 1):
        if current.referred_by_id is None:
            break
        referrer = db.query(Affiliate).filter(Affiliate.id == current.referred_by_id).first()
        if not referrer:
            break

        rate = COMMISSION_RATES[level]
        amount = (subscription_amount * rate).quantize(Decimal("0.01"))

        commission = Commission(
            earner_id=referrer.id,
            source_id=new_affiliate_id,
            amount=amount,
            tier=level,
            description=f"Level {level} commission from {affiliate.name}'s subscription",
            status="pending",
        )
        db.add(commission)

        # Update earner total_earnings
        referrer.total_earnings = (referrer.total_earnings or Decimal("0")) + amount
        created.append({
            "earner_name": referrer.name,
            "earner_email": referrer.email,
            "tier": level,
            "amount": amount,
        })

        current = referrer

    db.commit()
    return created


def get_affiliate_stats(affiliate_id: int, db: Session):
    """Compute stats for an affiliate."""
    now = datetime.now(timezone.utc)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    direct_referrals = db.query(Affiliate).filter(Affiliate.referred_by_id == affiliate_id).count()
    team_members = get_team_members(affiliate_id, db)
    team_size = len(team_members)

    affiliate = db.query(Affiliate).filter(Affiliate.id == affiliate_id).first()
    total_earnings = affiliate.total_earnings if affiliate else Decimal("0")

    pending_earnings = db.query(func.coalesce(func.sum(Commission.amount), 0)).filter(
        Commission.earner_id == affiliate_id,
        Commission.status == "pending",
    ).scalar() or Decimal("0")

    this_month_earnings = db.query(func.coalesce(func.sum(Commission.amount), 0)).filter(
        Commission.earner_id == affiliate_id,
        Commission.status == "pending",
        Commission.created_at >= month_start,
    ).scalar() or Decimal("0")

    return {
        "direct_referrals": direct_referrals,
        "team_size": team_size,
        "total_earnings": Decimal(str(total_earnings)),
        "pending_earnings": Decimal(str(pending_earnings)),
        "this_month_earnings": Decimal(str(this_month_earnings)),
    }
