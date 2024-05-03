CREATE TABLE IF NOT EXISTS assistant (
    assistant_id TEXT PRIMARY KEY NOT NULL, -- Manually ensure this is a UUID v4
    user_id TEXT NOT NULL,
    name TEXT NOT NULL,
    config TEXT NOT NULL, -- Store JSON data as text
    updated_at DATETIME DEFAULT (datetime('now')), -- Stores in UTC by default
    public BOOLEAN NOT NULL CHECK (public IN (0,1)) -- SQLite uses 0 and 1 for BOOLEAN
);

CREATE TABLE IF NOT EXISTS thread (
    thread_id TEXT PRIMARY KEY NOT NULL, -- Manually ensure this is a UUID v4
    assistant_id TEXT, -- Store as text and ensure it's a UUID in your application
    user_id TEXT NOT NULL,
    name TEXT NOT NULL,
    updated_at DATETIME DEFAULT (datetime('now')), -- Stores in UTC by default
    FOREIGN KEY (assistant_id) REFERENCES assistant(assistant_id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS checkpoints (
    thread_id TEXT NOT NULL,
    thread_ts DATETIME NOT NULL,
    parent_ts DATETIME,
    checkpoint BLOB, -- BLOB for binary data, assuming pickle serialization
    PRIMARY KEY (thread_id, thread_ts)
);
