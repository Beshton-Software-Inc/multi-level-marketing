"""Shared test helpers for creating ORM objects without hitting the real DB."""
from decimal import Decimal
from itertools import count

from app.models import Affiliate, SalesTeam, TeamMembership

_counter = count(1)


def make_affiliate(db, name: str, email: str, referred_by=None) -> Affiliate:
    aff = Affiliate(
        name=name,
        email=email,
        password_hash="fakehash",
        referral_code=f"TST{next(_counter):05d}",
        referred_by_id=referred_by.id if referred_by else None,
    )
    db.add(aff)
    db.flush()
    return aff


def make_team(
    db,
    name: str = "Team A",
    prefix: str = "TEAMA",
    commission_rate: int = 50,
    commission_mode: str = "default",
    unassigned_policy: str = "compress",
    **custom_rates,
) -> SalesTeam:
    """Create a SalesTeam.

    Pass custom_rate_l1=20, custom_rate_l2=5, etc. for custom mode.
    Values are in percent (e.g. 20 = 20%).
    """
    team = SalesTeam(
        name=name,
        referral_prefix=prefix,
        commission_rate=Decimal(str(commission_rate)),
        commission_mode=commission_mode,
        unassigned_policy=unassigned_policy,
        **{k: Decimal(str(v)) for k, v in custom_rates.items()},
    )
    db.add(team)
    db.flush()
    return team


def make_membership(db, team: SalesTeam, affiliate: Affiliate, role: str = "member") -> TeamMembership:
    m = TeamMembership(team_id=team.id, affiliate_id=affiliate.id, role=role)
    db.add(m)
    db.flush()
    return m
