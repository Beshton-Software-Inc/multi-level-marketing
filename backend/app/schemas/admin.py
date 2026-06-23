from pydantic import BaseModel, ConfigDict, field_validator
from typing import Optional, Literal, List
from decimal import Decimal
from datetime import datetime


class AdminStats(BaseModel):
    total_affiliates: int
    active_affiliates: int
    total_commissions: Decimal
    pending_payouts_amount: Decimal
    pending_payouts_count: int


class PayoutUpdateRequest(BaseModel):
    status: Literal["approved", "rejected"]
    admin_notes: Optional[str] = None


class ManualCommissionRequest(BaseModel):
    affiliate_email: str
    amount: Decimal
    description: str


class SimulateSubscriptionRequest(BaseModel):
    affiliate_email: str
    subscription_amount: Decimal = Decimal("100")


class SimulatedCommission(BaseModel):
    earner_name: str
    earner_email: str
    tier: int
    amount: Decimal


# ── Sales Team schemas ──────────────────────────────────────────────────────

class SalesTeamCreate(BaseModel):
    name: str
    referral_prefix: str
    commission_rate: Decimal = Decimal("100")
    notes: Optional[str] = None

    @field_validator("commission_rate")
    @classmethod
    def rate_in_range(cls, v: Decimal) -> Decimal:
        if not (Decimal("0") <= v <= Decimal("100")):
            raise ValueError("commission_rate must be between 0 and 100")
        return v

    @field_validator("referral_prefix")
    @classmethod
    def prefix_uppercase(cls, v: str) -> str:
        return v.strip().upper()


class SalesTeamUpdate(BaseModel):
    name: Optional[str] = None
    commission_rate: Optional[Decimal] = None
    notes: Optional[str] = None
    is_active: Optional[bool] = None

    @field_validator("commission_rate")
    @classmethod
    def rate_in_range(cls, v: Optional[Decimal]) -> Optional[Decimal]:
        if v is not None and not (Decimal("0") <= v <= Decimal("100")):
            raise ValueError("commission_rate must be between 0 and 100")
        return v


class TeamMemberInfo(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    affiliate_id: int
    role: str
    joined_at: datetime
    affiliate_name: Optional[str] = None
    affiliate_email: Optional[str] = None


class SalesTeamResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    referral_prefix: str
    commission_rate: Decimal
    is_active: bool
    notes: Optional[str] = None
    created_at: datetime
    member_count: int = 0


class SalesTeamDetailResponse(SalesTeamResponse):
    members: List[TeamMemberInfo] = []


class AddTeamMemberRequest(BaseModel):
    affiliate_email: str
    role: Literal["admin", "member"] = "member"


class SetTeamMemberRoleRequest(BaseModel):
    role: Literal["admin", "member"]
