-- Migration: add invite token columns to affiliates for team-admin invite flow.
-- Idempotent: safe to run multiple times.

ALTER TABLE affiliates
    ADD COLUMN IF NOT EXISTS invite_token VARCHAR(64) UNIQUE,
    ADD COLUMN IF NOT EXISTS invite_token_expires_at TIMESTAMPTZ;

CREATE INDEX IF NOT EXISTS ix_affiliates_invite_token ON affiliates(invite_token);
