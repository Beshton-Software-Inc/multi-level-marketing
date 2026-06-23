from sqlalchemy import Column, Integer, String, Boolean, Numeric, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class Affiliate(Base):
    __tablename__ = "affiliates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    referral_code = Column(String, unique=True, nullable=False, index=True)
    referred_by_id = Column(Integer, ForeignKey("affiliates.id"), nullable=True)
    status = Column(String, default="active")
    total_earnings = Column(Numeric(10, 2), default=0)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    referred_by = relationship("Affiliate", remote_side=[id], back_populates="referrals")
    referrals = relationship("Affiliate", back_populates="referred_by")
    commissions_earned = relationship("Commission", foreign_keys="Commission.earner_id", back_populates="earner")
    payout_requests = relationship("PayoutRequest", back_populates="affiliate")


class Commission(Base):
    __tablename__ = "commissions"

    id = Column(Integer, primary_key=True, index=True)
    earner_id = Column(Integer, ForeignKey("affiliates.id"), nullable=False)
    source_id = Column(Integer, ForeignKey("affiliates.id"), nullable=True)
    amount = Column(Numeric(10, 2), nullable=False)
    tier = Column(Integer, nullable=False)
    description = Column(String)
    status = Column(String, default="pending")  # pending, paid
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Snapshot columns — record the inputs used at creation time so that future
    # changes to commission rates or team allocation percentages never alter the
    # meaning of a past commission row.
    subscription_amount = Column(Numeric(10, 2), nullable=True)   # gross sub amount before any split
    commission_rate = Column(Numeric(6, 4), nullable=True)         # e.g. 0.2000 for the 20% L1 rate
    team_allocation_pct = Column(Numeric(5, 2), nullable=True)     # null until team system is added

    earner = relationship("Affiliate", foreign_keys=[earner_id], back_populates="commissions_earned")
    source = relationship("Affiliate", foreign_keys=[source_id])


class PayoutRequest(Base):
    __tablename__ = "payout_requests"

    id = Column(Integer, primary_key=True, index=True)
    affiliate_id = Column(Integer, ForeignKey("affiliates.id"), nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    status = Column(String, default="pending")  # pending, approved, rejected
    payment_method = Column(String)
    payment_details = Column(String)
    admin_notes = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    processed_at = Column(DateTime(timezone=True), nullable=True)

    affiliate = relationship("Affiliate", back_populates="payout_requests")
