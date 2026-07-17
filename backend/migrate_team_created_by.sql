-- Migration: track which affiliate created each sales team.
-- Used to determine all teams a team admin manages (primary + created).
-- Idempotent: safe to run multiple times.

ALTER TABLE sales_teams
    ADD COLUMN IF NOT EXISTS created_by_affiliate_id INTEGER
        REFERENCES affiliates(id) ON DELETE SET NULL;

CREATE INDEX IF NOT EXISTS ix_sales_teams_created_by_affiliate_id
    ON sales_teams(created_by_affiliate_id);
