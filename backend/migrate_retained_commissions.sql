-- Allow earner_id to be NULL on commissions so platform-retained rows can be
-- written instead of silently dropped/printed. earner_id = NULL with
-- status = 'retained' means WinWinLaw kept the amount (no affiliate upline).
ALTER TABLE commissions ALTER COLUMN earner_id DROP NOT NULL;

-- Add 'retained' as a recognised status alongside 'pending' and 'paid'.
-- (Column is VARCHAR with no CHECK constraint, so no schema change needed —
--  this comment documents the new allowed value for ops/reporting queries.)

-- Useful query to audit retained amounts:
-- SELECT subscription_id, SUM(amount) AS retained_total, COUNT(*) AS levels
-- FROM commissions
-- WHERE status = 'retained'
-- GROUP BY subscription_id
-- ORDER BY retained_total DESC;
