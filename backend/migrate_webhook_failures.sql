-- Create the webhook_failures table to record MLM webhook deliveries that
-- failed to process inside winwinlaw-mlm. Allows ops to inspect and replay.
-- Safe to run on a live DB — uses IF NOT EXISTS.

CREATE TABLE IF NOT EXISTS webhook_failures (
    id             SERIAL PRIMARY KEY,
    subscription_id VARCHAR NOT NULL,
    referral_code  VARCHAR NOT NULL,
    customer_email VARCHAR NOT NULL,
    payload        TEXT NOT NULL,
    error_message  TEXT NOT NULL,
    created_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    resolved       BOOLEAN NOT NULL DEFAULT FALSE,
    resolved_at    TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS ix_webhook_failures_subscription_id
    ON webhook_failures (subscription_id);

CREATE INDEX IF NOT EXISTS ix_webhook_failures_resolved
    ON webhook_failures (resolved);
