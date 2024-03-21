ALTER TABLE checkpoints
    DROP CONSTRAINT IF EXISTS checkpoints_pkey,
    ADD PRIMARY KEY (thread_id),
    DROP COLUMN IF EXISTS thread_ts,
    DROP COLUMN IF EXISTS parent_ts;
