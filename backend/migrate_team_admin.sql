-- Migration: add managed_team_id to affiliates for scoped team admin access.
-- Idempotent: safe to run multiple times.
--
-- is_admin=true + managed_team_id=NULL  → WWL super admin (full access)
-- is_admin=true + managed_team_id=<id> → team admin (scoped to that team only)

ALTER TABLE affiliates
    ADD COLUMN IF NOT EXISTS managed_team_id INTEGER
        REFERENCES sales_teams(id) ON DELETE SET NULL;

CREATE INDEX IF NOT EXISTS ix_affiliates_managed_team_id ON affiliates(managed_team_id);
