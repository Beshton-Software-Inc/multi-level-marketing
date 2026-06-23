-- Add commission mode, unassigned policy, and custom per-level rate columns to sales_teams.
-- Safe to run on a live DB — uses IF NOT EXISTS / ADD COLUMN IF NOT EXISTS.

ALTER TABLE sales_teams
    ADD COLUMN IF NOT EXISTS commission_mode   VARCHAR NOT NULL DEFAULT 'default',
    ADD COLUMN IF NOT EXISTS unassigned_policy VARCHAR NOT NULL DEFAULT 'compress',
    ADD COLUMN IF NOT EXISTS custom_rate_l1    NUMERIC(5, 2),
    ADD COLUMN IF NOT EXISTS custom_rate_l2    NUMERIC(5, 2),
    ADD COLUMN IF NOT EXISTS custom_rate_l3    NUMERIC(5, 2),
    ADD COLUMN IF NOT EXISTS custom_rate_l4    NUMERIC(5, 2),
    ADD COLUMN IF NOT EXISTS custom_rate_l5    NUMERIC(5, 2),
    ADD COLUMN IF NOT EXISTS custom_rate_l6    NUMERIC(5, 2),
    ADD COLUMN IF NOT EXISTS custom_rate_l7    NUMERIC(5, 2);
