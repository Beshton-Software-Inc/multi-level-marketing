from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Affiliate, ReferralCode, SalesTeam, TeamMembership
from app.schemas.auth import RegisterRequest, LoginRequest, TokenResponse, AffiliateInToken
from app.schemas.admin import AcceptInviteRequest
from app.services.auth_service import (
    hash_password, verify_password, create_access_token, generate_referral_code
)

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(body: RegisterRequest, db: Session = Depends(get_db)):
    existing = db.query(Affiliate).filter(Affiliate.email == body.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    # Find referrer if referral_code provided.
    # Accept both personal affiliate codes (affiliates.referral_code) and
    # team codes (referral_codes table) so dashboard-shared links work.
    referrer = None
    team_id_for_membership = None
    if body.referral_code:
        # 1. Check personal affiliate code
        referrer = db.query(Affiliate).filter(Affiliate.referral_code == body.referral_code).first()
        if referrer and referrer.managed_team_id:
            team_id_for_membership = referrer.managed_team_id

        if not referrer:
            # 2. Check team referral code — place registrant under the code's creator
            team_code = (
                db.query(ReferralCode)
                .filter(ReferralCode.code == body.referral_code, ReferralCode.is_active.is_(True))
                .first()
            )
            if team_code:
                team_id_for_membership = team_code.team_id
                if team_code.created_by_affiliate_id:
                    referrer = db.query(Affiliate).filter(Affiliate.id == team_code.created_by_affiliate_id).first()
                else:
                    # Fall back to the team's primary admin
                    referrer = (
                        db.query(Affiliate)
                        .filter(Affiliate.managed_team_id == team_code.team_id, Affiliate.is_admin.is_(True))
                        .first()
                    )

        if not referrer:
            raise HTTPException(status_code=400, detail="Invalid referral code")

    # Inherit the prefix from the referral code used to register (e.g. "NS" from "NS-XXXXXXXX")
    code_prefix = ""
    if body.referral_code and '-' in body.referral_code:
        code_prefix = body.referral_code.split('-')[0]

    # Generate unique referral code with the matching prefix
    while True:
        code = generate_referral_code(code_prefix)
        if not db.query(Affiliate).filter(Affiliate.referral_code == code).first():
            break

    affiliate = Affiliate(
        name=body.name,
        email=body.email,
        password_hash=hash_password(body.password),
        referral_code=code,
        referred_by_id=referrer.id if referrer else None,
    )
    db.add(affiliate)
    db.commit()
    db.refresh(affiliate)

    # Auto-enroll in team when registered via a team code or a team admin's personal code
    if team_id_for_membership:
        db.add(TeamMembership(team_id=team_id_for_membership, affiliate_id=affiliate.id, role="member"))
        db.commit()

    token = create_access_token({"sub": str(affiliate.id)})
    return TokenResponse(
        access_token=token,
        user=AffiliateInToken.model_validate(affiliate),
    )


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, db: Session = Depends(get_db)):
    affiliate = db.query(Affiliate).filter(Affiliate.email == body.email).first()
    if not affiliate or not verify_password(body.password, affiliate.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    if affiliate.status == "pending":
        raise HTTPException(status_code=403, detail="Account not activated. Check your invite email.")
    if affiliate.status != "active":
        raise HTTPException(status_code=403, detail="Account suspended")

    token = create_access_token({"sub": str(affiliate.id)})
    return TokenResponse(
        access_token=token,
        user=AffiliateInToken.model_validate(affiliate),
    )


@router.post("/accept-invite", response_model=TokenResponse)
def accept_invite(body: AcceptInviteRequest, db: Session = Depends(get_db)):
    """Team admin sets their password using the token from their invite email."""
    affiliate = db.query(Affiliate).filter(Affiliate.invite_token == body.token).first()
    if not affiliate:
        raise HTTPException(status_code=400, detail="Invalid or already used invite link")
    if affiliate.invite_token_expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="Invite link has expired. Ask a super admin to resend.")
    if len(body.password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")

    affiliate.password_hash = hash_password(body.password)
    affiliate.status = "active"
    affiliate.invite_token = None
    affiliate.invite_token_expires_at = None
    db.commit()
    db.refresh(affiliate)

    token = create_access_token({"sub": str(affiliate.id)})
    return TokenResponse(
        access_token=token,
        user=AffiliateInToken.model_validate(affiliate),
    )
