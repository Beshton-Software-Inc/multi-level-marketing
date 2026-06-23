from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from decimal import Decimal
from datetime import datetime


class AffiliateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: str
    referral_code: str
    referred_by_id: Optional[int] = None
    status: str
    total_earnings: Decimal
    is_admin: bool
    created_at: datetime


class AffiliateStats(BaseModel):
    direct_referrals: int
    team_size: int
    total_earnings: Decimal
    pending_earnings: Decimal
    this_month_earnings: Decimal


class CommissionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    earner_id: int
    source_id: Optional[int] = None
    source_name: Optional[str] = None
    amount: Decimal
    tier: int
    description: Optional[str] = None
    status: str
    created_at: datetime
    # Snapshot fields — reflect the exact inputs used when this commission was created
    subscription_amount: Optional[Decimal] = None
    commission_rate: Optional[Decimal] = None
    team_allocation_pct: Optional[Decimal] = None


class PayoutRequestCreate(BaseModel):
    amount: Decimal
    payment_method: str
    payment_details: str


class PayoutRequestResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    affiliate_id: int
    amount: Decimal
    status: str
    payment_method: Optional[str] = None
    payment_details: Optional[str] = None
    admin_notes: Optional[str] = None
    created_at: datetime
    processed_at: Optional[datetime] = None


class TeamMember(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: str
    referral_code: str
    status: str
    total_earnings: Decimal
    created_at: datetime
    depth: int
    direct_referrals: int
