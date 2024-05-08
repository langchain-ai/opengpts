ALTER TABLE thread
ADD COLUMN metadata JSONB;

UPDATE thread
SET metadata = json_build_object(
    'assistant_type', (SELECT config->'configurable'->>'type'
                 FROM assistant
                 WHERE assistant.assistant_id = thread.assistant_id)
);