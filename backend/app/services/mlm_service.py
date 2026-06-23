from decimal import Decimal
from datetime import datetime, timezone
from typing import List, Dict, Any

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import Affiliate, Commission


# Commission rates by level (7-level structure)
COMMISSION_RATES = {
    1: Decimal("0.20"),  # 20% — direct
    2: Decimal("0.05"),  # 5%
    3: Decimal("0.05"),  # 5%
    4: Decimal("0.03"),  # 3%
    5: Decimal("0.02"),  # 2%
    6: Decimal("0.05"),  # 5%
    7: Decimal("0.10"),  # 10%
}
MAX_LEVELS = 7


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


def _walk_ancestors(affiliate: "Affiliate", db: Session) -> List["Affiliate"]:
    """Walk the referral chain upward and return all ancestors in order.

    ancestors[0] = direct referrer (L1), ancestors[1] = L2, etc.
    Stops at MAX_LEVELS or when the chain ends.
    """
    ancestors: List["Affiliate"] = []
    current = affiliate
    for _ in range(MAX_LEVELS):
        if current.referred_by_id is None:
            break
        referrer = db.query(Affiliate).filter(Affiliate.id == current.referred_by_id).first()
        if not referrer:
            break
        ancestors.append(referrer)
        current = referrer
    return ancestors


def preview_commission_breakdown(
    buyer_affiliate_id: int,
    subscription_amount: Decimal,
    db: Session,
    team_commission_rate: Decimal = Decimal("100"),
) -> List[Dict[str, Any]]:
    """Return estimated commissions for all 7 levels without persisting.

    Uses compression: if a level has no natural earner, its commission is
    assigned to the topmost ancestor that exists. If there is no upline at
    all, the amount is marked as retained by WinWinLaw.
    """
    affiliate = db.query(Affiliate).filter(Affiliate.id == buyer_affiliate_id).first()
    if not affiliate:
        return []

    team_share = (subscription_amount * team_commission_rate / Decimal("100")).quantize(Decimal("0.01"))
    ancestors = _walk_ancestors(affiliate, db)

    breakdown: List[Dict[str, Any]] = []
    for level in range(1, MAX_LEVELS + 1):
        rate = COMMISSION_RATES[level]
        amount = (team_share * rate).quantize(Decimal("0.01"))
        natural_idx = level - 1

        if natural_idx < len(ancestors):
            earner = ancestors[natural_idx]
            compressed = False
            compressed_from_level = None
        elif ancestors:
            earner = ancestors[-1]
            compressed = True
            compressed_from_level = len(ancestors)
        else:
            breakdown.append({
                "earner_name": "WinWinLaw (no upline)",
                "earner_email": None,
                "tier": level,
                "amount": amount,
                "commission_rate": rate,
                "subscription_amount": subscription_amount,
                "team_commission_rate": team_commission_rate,
                "team_share": team_share,
                "compressed": False,
                "compressed_from_level": None,
                "retained_by_platform": True,
            })
            continue

        breakdown.append({
            "earner_name": earner.name,
            "earner_email": earner.email,
            "tier": level,
            "amount": amount,
            "commission_rate": rate,
            "subscription_amount": subscription_amount,
            "team_commission_rate": team_commission_rate,
            "team_share": team_share,
            "compressed": compressed,
            "compressed_from_level": compressed_from_level,
            "retained_by_platform": False,
        })

    return breakdown


def calculate_and_create_commissions(
    new_affiliate_id: int,
    subscription_amount: Decimal,
    db: Session,
    team_commission_rate: Decimal = Decimal("100"),
) -> List[Dict[str, Any]]:
    """Create commission records for all 7 levels using compression.

    For each level:
    - Natural earner exists → they receive the commission normally.
    - Chain topped out → commission compresses to the topmost ancestor.
    - No upline at all → WinWinLaw retains it (logged, never silently dropped).

    team_commission_rate: % of subscription_amount the team's cascade distributes.
    Defaults to 100 so callers without a team assignment are unaffected.
    """
    affiliate = db.query(Affiliate).filter(Affiliate.id == new_affiliate_id).first()
    if not affiliate:
        return []

    team_share = (subscription_amount * team_commission_rate / Decimal("100")).quantize(Decimal("0.01"))
    ancestors = _walk_ancestors(affiliate, db)

    created: List[Dict[str, Any]] = []
    winwinlaw_retained: List[Dict[str, Any]] = []

    for level in range(1, MAX_LEVELS + 1):
        rate = COMMISSION_RATES[level]
        amount = (team_share * rate).quantize(Decimal("0.01"))
        natural_idx = level - 1

        if natural_idx < len(ancestors):
            earner = ancestors[natural_idx]
            compressed = False
            desc = f"Level {level} commission from {affiliate.name}'s subscription"
        elif ancestors:
            # Compress to topmost ancestor
            earner = ancestors[-1]
            compressed = True
            filled_depth = len(ancestors)
            desc = (
                f"Level {level} commission (compressed to L{filled_depth}) "
                f"from {affiliate.name}'s subscription"
            )
        else:
            # No upline whatsoever — retained by WinWinLaw
            winwinlaw_retained.append({"level": level, "amount": amount})
            continue

        commission = Commission(
            earner_id=earner.id,
            source_id=new_affiliate_id,
            amount=amount,
            tier=level,
            description=desc,
            status="pending",
            subscription_amount=subscription_amount,
            commission_rate=rate,
            team_allocation_pct=team_commission_rate,
        )
        db.add(commission)
        earner.total_earnings = (earner.total_earnings or Decimal("0")) + amount

        created.append({
            "earner_name": earner.name,
            "earner_email": earner.email,
            "tier": level,
            "amount": amount,
            "commission_rate": rate,
            "subscription_amount": subscription_amount,
            "team_commission_rate": team_commission_rate,
            "compressed": compressed,
        })

    if winwinlaw_retained:
        total_retained = sum(r["amount"] for r in winwinlaw_retained)
        levels = [r["level"] for r in winwinlaw_retained]
        print(
            f"[MLM] Platform retained ${total_retained} from levels {levels} "
            f"— {affiliate.name} (id={affiliate.id}) has no upline"
        )

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
