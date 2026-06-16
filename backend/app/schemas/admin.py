from pydantic import BaseModel
from typing import Optional, Literal
from decimal import Decimal


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
