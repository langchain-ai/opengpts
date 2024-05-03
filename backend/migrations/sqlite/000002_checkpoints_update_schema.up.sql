-- Step 2: Update the newly added columns with current UTC datetime where they are NULL.
-- This assumes you handle NULL values appropriately in your application if these columns are expected to have meaningful timestamps.
UPDATE checkpoints
SET thread_ts = datetime('now')
WHERE thread_ts IS NULL;

-- Since SQLite does not allow altering a table to drop or add a primary key constraint directly,
-- you need to create a new table with the desired structure, copy the data, drop the old table, and rename the new one.

-- Step 3: Create a new table with the correct structure and primary key.
CREATE TABLE IF NOT EXISTS new_checkpoints (
    thread_id TEXT NOT NULL,
    thread_ts DATETIME NOT NULL,
    parent_ts DATETIME,
    checkpoint BLOB,
    PRIMARY KEY (thread_id, thread_ts)
);

-- Step 4: Copy data from the old table to the new table.
INSERT INTO new_checkpoints (thread_id, thread_ts, parent_ts, checkpoint)
SELECT thread_id, thread_ts, parent_ts, checkpoint FROM checkpoints;

-- Step 5: Drop the old table.
DROP TABLE checkpoints;

-- Step 6: Rename the new table to the original table's name.
ALTER TABLE new_checkpoints RENAME TO checkpoints;
