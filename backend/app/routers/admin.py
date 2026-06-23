from datetime import datetime, timezone
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Affiliate, Commission, PayoutRequest, SalesTeam, TeamMembership, WebhookFailure
from app.schemas.admin import (
    AdminStats,
    PayoutUpdateRequest,
    ManualCommissionRequest,
    SimulateSubscriptionRequest,
    SimulatedCommission,
    SalesTeamCreate,
    SalesTeamUpdate,
    SalesTeamResponse,
    SalesTeamDetailResponse,
    TeamMemberInfo,
    AddTeamMemberRequest,
    SetTeamMemberRoleRequest,
    CommissionConfigResponse,
    CommissionConfigUpdate,
)
from app.schemas.affiliate import AffiliateResponse, PayoutRequestResponse
from app.services.auth_service import require_admin
from app.services.mlm_service import build_effective_rates, preview_commission_breakdown

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

    team_commission_rate = Decimal("100")
    commission_rates = None
    unassigned_policy = "compress"
    team_admin_id = None

    membership = db.query(TeamMembership).filter(TeamMembership.affiliate_id == affiliate.id).first()
    if membership and membership.team and membership.team.is_active:
        team = membership.team
        team_commission_rate = Decimal(str(team.commission_rate))
        commission_rates = build_effective_rates(team)
        unassigned_policy = team.unassigned_policy or "compress"
        if unassigned_policy == "retain_admin":
            admin_m = db.query(TeamMembership).filter(
                TeamMembership.team_id == team.id,
                TeamMembership.role == "admin",
            ).first()
            if admin_m:
                team_admin_id = admin_m.affiliate_id

    breakdown = preview_commission_breakdown(
        affiliate.id,
        body.subscription_amount,
        db,
        team_commission_rate,
        commission_rates=commission_rates,
        unassigned_policy=unassigned_policy,
        team_admin_id=team_admin_id,
    )
    commissions = [SimulatedCommission.model_validate(c) for c in breakdown]

    if not commissions:
        return {
            "message": f"No upline found for {affiliate.name} — no commissions would be earned.",
            "buyer_name": affiliate.name,
            "buyer_email": affiliate.email,
            "subscription_amount": body.subscription_amount,
            "team_commission_rate": float(team_commission_rate),
            "commissions": [],
        }

    return {
        "message": f"Estimated commissions for a ${body.subscription_amount} subscription by {affiliate.name} (not saved)",
        "buyer_name": affiliate.name,
        "buyer_email": affiliate.email,
        "subscription_amount": body.subscription_amount,
        "team_commission_rate": float(team_commission_rate),
        "commissions": commissions,
    }


# ── Sales Team management ───────────────────────────────────────────────────

def _team_response(team: SalesTeam) -> dict:
    return {
        "id": team.id,
        "name": team.name,
        "referral_prefix": team.referral_prefix,
        "commission_rate": team.commission_rate,
        "is_active": team.is_active,
        "notes": team.notes,
        "created_at": team.created_at,
        "member_count": len(team.members),
    }


@router.get("/teams")
def list_teams(admin: Affiliate = Depends(require_admin), db: Session = Depends(get_db)):
    """List all sales teams with their commission rates and member counts."""
    teams = db.query(SalesTeam).order_by(SalesTeam.created_at.desc()).all()
    return {"teams": [_team_response(t) for t in teams]}


@router.post("/teams", status_code=201)
def create_team(
    body: SalesTeamCreate,
    admin: Affiliate = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Create a new sales team and assign its commission rate."""
    if db.query(SalesTeam).filter(SalesTeam.name == body.name).first():
        raise HTTPException(status_code=400, detail="A team with this name already exists")
    if db.query(SalesTeam).filter(SalesTeam.referral_prefix == body.referral_prefix).first():
        raise HTTPException(status_code=400, detail="A team with this referral prefix already exists")

    team = SalesTeam(
        name=body.name,
        referral_prefix=body.referral_prefix,
        commission_rate=body.commission_rate,
        notes=body.notes,
    )
    db.add(team)
    db.commit()
    db.refresh(team)
    return _team_response(team)


@router.get("/teams/{team_id}")
def get_team(
    team_id: int,
    admin: Affiliate = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Get a team with its full member list."""
    team = db.query(SalesTeam).filter(SalesTeam.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    members = []
    for m in team.members:
        members.append({
            "affiliate_id": m.affiliate_id,
            "role": m.role,
            "joined_at": m.joined_at,
            "affiliate_name": m.affiliate.name if m.affiliate else None,
            "affiliate_email": m.affiliate.email if m.affiliate else None,
        })

    return {**_team_response(team), "members": members}


@router.put("/teams/{team_id}")
def update_team(
    team_id: int,
    body: SalesTeamUpdate,
    admin: Affiliate = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Update a team's commission rate, name, notes, or active status."""
    team = db.query(SalesTeam).filter(SalesTeam.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    if body.name is not None:
        if db.query(SalesTeam).filter(SalesTeam.name == body.name, SalesTeam.id != team_id).first():
            raise HTTPException(status_code=400, detail="A team with this name already exists")
        team.name = body.name
    if body.commission_rate is not None:
        team.commission_rate = body.commission_rate
    if body.notes is not None:
        team.notes = body.notes
    if body.is_active is not None:
        team.is_active = body.is_active

    db.commit()
    db.refresh(team)
    return _team_response(team)


@router.post("/teams/{team_id}/members", status_code=201)
def add_team_member(
    team_id: int,
    body: AddTeamMemberRequest,
    admin: Affiliate = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Add an affiliate to a team. Each affiliate can belong to only one team."""
    team = db.query(SalesTeam).filter(SalesTeam.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    affiliate = db.query(Affiliate).filter(Affiliate.email == body.affiliate_email).first()
    if not affiliate:
        raise HTTPException(status_code=404, detail="Affiliate not found")

    existing = db.query(TeamMembership).filter(TeamMembership.affiliate_id == affiliate.id).first()
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Affiliate is already a member of team '{existing.team.name}'. Remove them first.",
        )

    membership = TeamMembership(team_id=team_id, affiliate_id=affiliate.id, role=body.role)
    db.add(membership)
    db.commit()
    return {
        "message": f"{affiliate.name} added to {team.name} as {body.role}",
        "affiliate_id": affiliate.id,
        "team_id": team_id,
        "role": body.role,
    }


@router.put("/teams/{team_id}/members/{affiliate_id}")
def update_team_member_role(
    team_id: int,
    affiliate_id: int,
    body: SetTeamMemberRoleRequest,
    admin: Affiliate = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Change a team member's role between admin and member."""
    membership = db.query(TeamMembership).filter(
        TeamMembership.team_id == team_id,
        TeamMembership.affiliate_id == affiliate_id,
    ).first()
    if not membership:
        raise HTTPException(status_code=404, detail="Membership not found")

    membership.role = body.role
    db.commit()
    return {"message": f"Role updated to {body.role}", "affiliate_id": affiliate_id, "team_id": team_id}


@router.delete("/teams/{team_id}/members/{affiliate_id}")
def remove_team_member(
    team_id: int,
    affiliate_id: int,
    admin: Affiliate = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Remove an affiliate from a team."""
    membership = db.query(TeamMembership).filter(
        TeamMembership.team_id == team_id,
        TeamMembership.affiliate_id == affiliate_id,
    ).first()
    if not membership:
        raise HTTPException(status_code=404, detail="Membership not found")

    affiliate_name = membership.affiliate.name if membership.affiliate else str(affiliate_id)
    team_name = membership.team.name if membership.team else str(team_id)
    db.delete(membership)
    db.commit()
    return {"message": f"{affiliate_name} removed from {team_name}"}


@router.get("/teams/{team_id}/commission-config", response_model=CommissionConfigResponse)
def get_commission_config(
    team_id: int,
    admin: Affiliate = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Return a team's commission mode, unassigned policy, and custom per-level rates."""
    team = db.query(SalesTeam).filter(SalesTeam.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    return CommissionConfigResponse.model_validate(team)


@router.put("/teams/{team_id}/commission-config", response_model=CommissionConfigResponse)
def update_commission_config(
    team_id: int,
    body: CommissionConfigUpdate,
    admin: Affiliate = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Update a team's commission mode, unassigned policy, and/or custom per-level rates.

    Send only the fields you want to change — omitted fields are left as-is.
    custom_rate_lN values are stored as percentages (e.g. 20 = 20%).
    They are only used when commission_mode is set to "custom".
    """
    team = db.query(SalesTeam).filter(SalesTeam.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    update_data = body.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(team, field, value)

    db.commit()
    db.refresh(team)
    return CommissionConfigResponse.model_validate(team)


# ── Webhook failure management ───────────────────────────────────────────────

@router.get("/webhook-failures")
def list_webhook_failures(
    resolved: Optional[bool] = None,
    admin: Affiliate = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """List webhook failures. Pass ?resolved=false to see only open failures."""
    q = db.query(WebhookFailure).order_by(WebhookFailure.created_at.desc())
    if resolved is not None:
        q = q.filter(WebhookFailure.resolved == resolved)
    failures = q.all()
    return {
        "failures": [
            {
                "id": f.id,
                "subscription_id": f.subscription_id,
                "referral_code": f.referral_code,
                "customer_email": f.customer_email,
                "error_message": f.error_message,
                "payload": f.payload,
                "created_at": f.created_at,
                "resolved": f.resolved,
                "resolved_at": f.resolved_at,
            }
            for f in failures
        ],
        "total": len(failures),
    }


@router.post("/webhook-failures/{failure_id}/resolve")
def resolve_webhook_failure(
    failure_id: int,
    admin: Affiliate = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Mark a webhook failure as resolved after manually replaying it."""
    from datetime import datetime, timezone
    failure = db.query(WebhookFailure).filter(WebhookFailure.id == failure_id).first()
    if not failure:
        raise HTTPException(status_code=404, detail="Webhook failure not found")
    if failure.resolved:
        return {"message": "Already resolved", "id": failure_id}
    failure.resolved = True
    failure.resolved_at = datetime.now(timezone.utc)
    db.commit()
    return {"message": "Marked as resolved", "id": failure_id, "subscription_id": failure.subscription_id}
