-- Migration: referral_codes registry for MLM-owned code generation
-- Idempotent: safe to run multiple times.
--
-- Each row is one team-level referral code generated via the admin portal.
-- Format: {PREFIX}-{8 random alphanum}, e.g. NS-A3KX9Q7B.
-- On create/deactivate the backend syncs the event to the WWL platform so
-- WWL can resolve codes at subscription time without calling back to MLM.

CREATE TABLE IF NOT EXISTS referral_codes (
    id                      SERIAL PRIMARY KEY,
    code                    VARCHAR(20) UNIQUE NOT NULL,
    team_id                 INTEGER NOT NULL REFERENCES sales_teams(id) ON DELETE CASCADE,
    created_by_affiliate_id INTEGER REFERENCES affiliates(id) ON DELETE SET NULL,
    notes                   VARCHAR,
    is_active               BOOLEAN NOT NULL DEFAULT true,
    created_at              TIMESTAMPTZ NOT NULL DEFAULT now(),
    deactivated_at          TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS ix_referral_codes_code    ON referral_codes(code);
CREATE INDEX IF NOT EXISTS ix_referral_codes_team_id ON referral_codes(team_id);
CREATE INDEX IF NOT EXISTS ix_referral_codes_active  ON referral_codes(is_active);
