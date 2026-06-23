-- Run this once to create the sales_teams and team_memberships tables.
-- Safe to run on a live DB — uses IF NOT EXISTS.

CREATE TABLE IF NOT EXISTS sales_teams (
    id               SERIAL PRIMARY KEY,
    name             VARCHAR UNIQUE NOT NULL,
    referral_prefix  VARCHAR(8) UNIQUE NOT NULL,
    commission_rate  NUMERIC(5, 2) NOT NULL DEFAULT 0,
    is_active        BOOLEAN NOT NULL DEFAULT TRUE,
    notes            VARCHAR,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS team_memberships (
    id           SERIAL PRIMARY KEY,
    team_id      INTEGER NOT NULL REFERENCES sales_teams(id),
    affiliate_id INTEGER NOT NULL REFERENCES affiliates(id),
    role         VARCHAR NOT NULL DEFAULT 'member',
    joined_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_one_team_per_affiliate UNIQUE (affiliate_id)
);
