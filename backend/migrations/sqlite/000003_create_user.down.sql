-- SQLite doesn't support ALTER TABLE to drop constraints or change column types directly.
-- Similar to the "up" migration, if you need to reverse the changes,
-- you would have to recreate each table without the foreign keys and with the original column types.

-- For "assistant" and "thread", remove the foreign keys by recreating the tables without them.
-- Follow a similar process as described in the "up" migration, but omit the FOREIGN KEY definitions.

-- Drop the "user" table.
DROP TABLE IF EXISTS "user";