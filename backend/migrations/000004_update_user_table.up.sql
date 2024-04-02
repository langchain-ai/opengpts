
-- Update the column definition to allow NULL values for last_login_date
ALTER TABLE "user"
ALTER COLUMN last_login_date DROP NOT NULL;

-- Set default values for existing rows where last_login_date is NULL
UPDATE "user"
SET last_login_date = CURRENT_TIMESTAMP
WHERE last_login_date IS NULL;

-- Modify the last_login_date column to use CURRENT_TIMESTAMP as the default value
ALTER TABLE "user"
ALTER COLUMN last_login_date SET DEFAULT CURRENT_TIMESTAMP;