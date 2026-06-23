-- Run this once against your database to add the snapshot columns to existing
-- commission rows. Safe to run on a live DB — all three columns are nullable
-- so existing rows remain valid with NULL values.

ALTER TABLE commissions
    ADD COLUMN IF NOT EXISTS subscription_amount NUMERIC(10, 2),
    ADD COLUMN IF NOT EXISTS commission_rate      NUMERIC(6, 4),
    ADD COLUMN IF NOT EXISTS team_allocation_pct  NUMERIC(5, 2);
