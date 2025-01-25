-- BREAKING CHANGE WARNING:
-- This migration represents a transition from pickle-based checkpointing to a new checkpoint system.
-- As a result, any threads created before this migration will not be usable/clickable in the UI.
-- old thread data remains in old_checkpoints table but cannot be accessed by the new version.

-- Rename existing checkpoints table to preserve current data
-- This is necessary because the application will create a new checkpoints table
-- with an updated schema during runtime initialization.
ALTER TABLE checkpoints RENAME TO old_checkpoints;