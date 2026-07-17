import logging
import random
import string
from datetime import datetime, timezone

import httpx
from sqlalchemy.orm import Session

from app.config import settings
from app.models import Affiliate, ReferralCode, SalesTeam

log = logging.getLogger(__name__)

_CHARSET    = string.ascii_uppercase + string.digits
_SUFFIX_LEN = 8
_MAX_TRIES  = 10


def generate_code(
    db: Session,
    team: SalesTeam,
    created_by: Affiliate | None = None,
    notes: str | None = None,
) -> ReferralCode:
    """Generate {PREFIX}-{8 random alphanum}, persist to MLM DB, then sync to WWL."""
    if not team.referral_prefix:
        raise ValueError(f"Team '{team.name}' has no referral_prefix set.")
    for _ in range(_MAX_TRIES):
        suffix = "".join(random.choices(_CHARSET, k=_SUFFIX_LEN))
        code   = f"{team.referral_prefix}-{suffix}"
        if not db.query(ReferralCode).filter(ReferralCode.code == code).first():
            entry = ReferralCode(
                code=code,
                team_id=team.id,
                created_by_affiliate_id=created_by.id if created_by else None,
                notes=notes,
            )
            db.add(entry)
            db.commit()
            db.refresh(entry)
            _sync_to_wwl("create", code, notes)
            return entry
    raise RuntimeError("Could not generate a unique referral code after 10 attempts.")


def deactivate_code(db: Session, code_id: int) -> ReferralCode:
    """Deactivate a code in MLM DB and sync the deactivation to WWL."""
    entry = db.query(ReferralCode).filter(ReferralCode.id == code_id).first()
    if not entry:
        raise ValueError("Referral code not found.")
    entry.is_active = False
    entry.deactivated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(entry)
    _sync_to_wwl("deactivate", entry.code)
    return entry


def _sync_to_wwl(action: str, code: str, notes: str | None = None) -> None:
    """Push a create/deactivate event to WWL's internal sync endpoint.
    Fire-and-forget: logs on failure but never raises — a sync hiccup must not
    roll back the MLM-side operation."""
    url = f"{settings.WWL_INTERNAL_URL.rstrip('/')}/api/internal/referral-codes/sync"
    payload = {"action": action, "code": code, "notes": notes}
    try:
        with httpx.Client(timeout=10) as client:
            resp = client.post(
                url,
                json=payload,
                headers={"X-Sync-Secret": settings.WWL_SYNC_SECRET},
            )
        if resp.status_code not in (200, 204):
            log.error("WWL sync failed action=%s code=%s status=%s body=%s",
                      action, code, resp.status_code, resp.text[:200])
    except Exception as exc:
        log.error("WWL sync error action=%s code=%s: %s", action, code, exc)
