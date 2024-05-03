-- Step 1: Create a new temporary table that reflects the desired final structure,
-- excluding thread_ts and parent_ts columns, and setting thread_id as the primary key.
CREATE TABLE IF NOT EXISTS temp_checkpoints (
    thread_id TEXT NOT NULL,
    checkpoint BLOB,
    PRIMARY KEY (thread_id)
);

-- Step 2: Copy relevant data from the original table to the temporary table.
-- Since thread_ts and parent_ts are being dropped, they are not included in the copy.
INSERT INTO temp_checkpoints (thread_id, checkpoint)
SELECT thread_id, checkpoint FROM checkpoints;

-- Step 3: Drop the original checkpoints table.
DROP TABLE checkpoints;

-- Step 4: Rename the temporary table to 'checkpoints', effectively recreating the original table structure.
ALTER TABLE temp_checkpoints RENAME TO checkpoints;
