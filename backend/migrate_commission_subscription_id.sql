-- Run this once against your database to add the subscription_id column to
-- existing commission rows. Safe to run on a live DB — the column is nullable
-- so existing rows remain valid with NULL values.
--
-- Lets the /api/webhook/subscription handler detect a retried delivery for a
-- subscription it already paid commissions for, and no-op instead of paying
-- the cascade out a second time.

ALTER TABLE commissions
    ADD COLUMN IF NOT EXISTS subscription_id VARCHAR;

CREATE INDEX IF NOT EXISTS ix_commissions_subscription_id ON commissions (subscription_id);
