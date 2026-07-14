"""Shared test helpers for creating ORM objects without hitting the real DB."""
from decimal import Decimal
from itertools import count
from typing import Optional

from app.models import Affiliate, Commission, SalesTeam, TeamMembership

_counter = count(1)


def make_affiliate(
    db,
    name: str,
    email: str,
    referred_by=None,
    password: Optional[str] = None,
    is_admin: bool = False,
    status: str = "active",
    total_earnings=Decimal("0"),
) -> Affiliate:
    """Create an Affiliate.

    Pass password="plaintext" to get a real bcrypt hash (needed for login
    tests); otherwise a cheap placeholder hash is used since most tests never
    verify a password.
    """
    if password is not None:
        from app.services.auth_service import hash_password
        password_hash = hash_password(password)
    else:
        password_hash = "fakehash"

    aff = Affiliate(
        name=name,
        email=email,
        password_hash=password_hash,
        referral_code=f"TST{next(_counter):05d}",
        referred_by_id=referred_by.id if referred_by else None,
        is_admin=is_admin,
        status=status,
        total_earnings=Decimal(str(total_earnings)),
    )
    db.add(aff)
    db.flush()
    return aff


def make_commission(
    db,
    earner: Affiliate,
    source: Optional[Affiliate] = None,
    amount=Decimal("10.00"),
    tier: int = 1,
    status: str = "pending",
    subscription_id: Optional[str] = None,
) -> Commission:
    c = Commission(
        earner_id=earner.id,
        source_id=source.id if source else None,
        amount=Decimal(str(amount)),
        tier=tier,
        status=status,
        subscription_id=subscription_id,
    )
    db.add(c)
    db.flush()
    return c


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


def auth_headers(affiliate: Affiliate) -> dict:
    """Bearer-token header for hitting authenticated endpoints as `affiliate`."""
    from app.services.auth_service import create_access_token
    token = create_access_token({"sub": str(affiliate.id)})
    return {"Authorization": f"Bearer {token}"}
