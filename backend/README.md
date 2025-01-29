# backend

## Database Migrations

### Migration 5 - Checkpoint Management Update
This migration introduces a significant change to thread checkpoint management:

#### Changes
- Transitions from single-table pickle storage to a robust multi-table checkpoint management system
- Implements LangGraph's latest checkpoint architecture for improved state persistence
- Preserves existing checkpoint data by renaming `checkpoints` table to `old_checkpoints`
- Introduces three new tables for better checkpoint management:
  - `checkpoints`: Core checkpoint metadata
  - `checkpoint_blobs`: Actual checkpoint data storage (compatible with LangGraph state serialization)
  - `checkpoint_writes`: Tracks checkpoint write operations
- Adds runtime initialization via `ensure_setup()` in the lifespan event

#### Impact
- **Breaking Change**: Historical threads/checkpoints (pre-migration) will not be accessible in the UI
- Previous checkpoint data remains preserved but inaccessible in the new system
- Designed to work seamlessly with LangGraph's state persistence requirements

#### Migration Details
- **Up Migration**: Safely preserves existing data by renaming the table
- **Down Migration**: Restores original table structure if needed
- New checkpoint management tables are automatically created at application startup
