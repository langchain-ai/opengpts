ALTER TABLE checkpoints
    ADD COLUMN IF NOT EXISTS thread_ts TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS parent_ts TIMESTAMPTZ;

UPDATE checkpoints
    SET thread_ts = CURRENT_TIMESTAMP AT TIME ZONE 'UTC'
WHERE thread_ts IS NULL;

ALTER TABLE checkpoints
    DROP CONSTRAINT IF EXISTS checkpoints_pkey,
    ADD PRIMARY KEY (thread_id, thread_ts)
