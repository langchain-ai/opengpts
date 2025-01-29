-- Drop the blob storage table
DROP TABLE IF EXISTS checkpoint_blobs;

-- Drop the writes tracking table
DROP TABLE IF EXISTS checkpoint_writes;

-- Drop the new checkpoints table that was created by the application
DROP TABLE IF EXISTS checkpoints;

-- Restore the original checkpoints table by renaming old_checkpoints back
-- This preserves the original data that was saved before the migration
ALTER TABLE old_checkpoints RENAME TO checkpoints;