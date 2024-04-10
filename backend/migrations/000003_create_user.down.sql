ALTER TABLE assistant
    DROP CONSTRAINT fk_assistant_user_id,
    ALTER COLUMN user_id TYPE VARCHAR USING (user_id::text);

ALTER TABLE thread
    DROP CONSTRAINT fk_thread_user_id,
    ALTER COLUMN user_id TYPE VARCHAR USING (user_id::text);

DROP TABLE IF EXISTS "user";