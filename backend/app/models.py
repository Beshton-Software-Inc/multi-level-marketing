from sqlalchemy import Column, Integer, String, Boolean, Numeric, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class SalesTeam(Base):
    """A sales team managed by WinWinLaw. Each team has its own commission_rate —
    the percentage of every subscription they refer that flows into their MLM cascade.
    WinWinLaw retains (100 - commission_rate)% of each sale. Rates are independent
    per team; they do not need to sum to any total."""
    __tablename__ = "sales_teams"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    referral_prefix = Column(String(8), unique=True, nullable=False)  # e.g. "MRD" — team namespace
    commission_rate = Column(Numeric(5, 2), nullable=False, default=0)  # 0–100, e.g. 50.00 means team keeps 50%
    is_active = Column(Boolean, default=True)
    notes = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    members = relationship("TeamMembership", back_populates="team")


class TeamMembership(Base):
    """Links an affiliate to exactly one sales team with a role."""
    __tablename__ = "team_memberships"

    id = Column(Integer, primary_key=True, index=True)
    team_id = Column(Integer, ForeignKey("sales_teams.id"), nullable=False)
    affiliate_id = Column(Integer, ForeignKey("affiliates.id"), nullable=False)
    role = Column(String, default="member")  # "admin" | "member"
    joined_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (UniqueConstraint("affiliate_id", name="uq_one_team_per_affiliate"),)

    team = relationship("SalesTeam", back_populates="members")
    affiliate = relationship("Affiliate", back_populates="team_membership")


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
    team_membership = relationship("TeamMembership", back_populates="affiliate", uselist=False)


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
