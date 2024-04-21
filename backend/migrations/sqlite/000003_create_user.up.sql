-- Create the "user" table. Use TEXT for UUID and store timestamps as TEXT.
CREATE TABLE IF NOT EXISTS "user" (
    user_id TEXT PRIMARY KEY,
    sub TEXT UNIQUE NOT NULL,
    created_at DATETIME DEFAULT (datetime('now'))
);

-- Insert distinct users from the "assistant" table. 
-- SQLite doesn't support ON CONFLICT DO NOTHING in the same way, so use INSERT OR IGNORE.
-- The casting (user_id::uuid) isn't needed since we treat all UUIDs as TEXT.
INSERT OR IGNORE INTO "user" (user_id, sub)
SELECT DISTINCT user_id, user_id
FROM assistant
WHERE user_id IS NOT NULL;

-- Insert distinct users from the "thread" table.
INSERT OR IGNORE INTO "user" (user_id, sub)
SELECT DISTINCT user_id, user_id
FROM thread
WHERE user_id IS NOT NULL;

-- SQLite does not support adding foreign keys via ALTER TABLE.
-- You will need to recreate tables to add foreign key constraints, as shown previously.
-- Here's a simplified approach for "assistant" assuming dropping and recreating is acceptable.

-- Example for "assistant", assuming it's acceptable to drop & recreate it:
-- 1. Rename existing table.
ALTER TABLE assistant RENAME TO assistant_old;

-- 2. Create new table with foreign key constraint.
CREATE TABLE assistant (
    assistant_id TEXT PRIMARY KEY NOT NULL, -- Manually ensure this is a UUID v4
    user_id TEXT NOT NULL,
    name TEXT NOT NULL,
    config TEXT NOT NULL, -- Store JSON data as text
    updated_at DATETIME DEFAULT (datetime('now')), -- Stores in UTC by default
    public BOOLEAN NOT NULL CHECK (public IN (0,1)),
    FOREIGN KEY (user_id) REFERENCES "user" (user_id)
);

-- Version 3 - Create user table.
CREATE TABLE IF NOT EXISTS "user" (
    user_id TEXT PRIMARY KEY NOT NULL,
    sub TEXT UNIQUE NOT NULL,
    created_at DATETIME DEFAULT (datetime('now'))
);

-- 4. Drop old table.
DROP TABLE assistant_old;

-- Repeat similar steps for "thread" table to add the foreign key constraint.