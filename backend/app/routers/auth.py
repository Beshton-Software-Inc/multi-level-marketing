from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Affiliate
from app.schemas.auth import RegisterRequest, LoginRequest, TokenResponse, AffiliateInToken
from app.services.auth_service import (
    hash_password, verify_password, create_access_token, generate_referral_code
)

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(body: RegisterRequest, db: Session = Depends(get_db)):
    existing = db.query(Affiliate).filter(Affiliate.email == body.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    # Find referrer if referral_code provided
    referrer = None
    if body.referral_code:
        referrer = db.query(Affiliate).filter(Affiliate.referral_code == body.referral_code).first()
        if not referrer:
            raise HTTPException(status_code=400, detail="Invalid referral code")

    # Generate unique referral code
    while True:
        code = generate_referral_code()
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
    if affiliate.status != "active":
        raise HTTPException(status_code=403, detail="Account suspended")

    token = create_access_token({"sub": str(affiliate.id)})
    return TokenResponse(
        access_token=token,
        user=AffiliateInToken.model_validate(affiliate),
    )
