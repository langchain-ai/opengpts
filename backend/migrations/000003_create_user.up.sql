CREATE TABLE IF NOT EXISTS "user" (
    user_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    sub VARCHAR(255) UNIQUE NOT NULL
);

ALTER TABLE assistant
    DROP COLUMN user_id,
    ADD COLUMN user_id UUID REFERENCES "user"(user_id);

ALTER TABLE thread
    DROP COLUMN user_id,
    ADD COLUMN user_id UUID REFERENCES "user"(user_id);