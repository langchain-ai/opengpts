from pydantic import BaseModel

import orjson


class BaseStorage(BaseModel):
    """Storage Interface"""

    def __init__(self):
        super().__init__()

    def assistants_list_key(self, user_id: str):
        return f"opengpts:{user_id}:assistants"

    def assistant_key(self, user_id: str, assistant_id: str):
        """create key for assistant"""
        return f"opengpts:{user_id}:assistant:{assistant_id}"

    def threads_list_key(self, user_id: str):
        """create threads key"""
        return f"opengpts:{user_id}:threads"

    def thread_key(self, user_id: str, thread_id: str):
        """create thread key"""
        return f"opengpts:{user_id}:thread:{thread_id}"

    def thread_messages_key(self, user_id: str, thread_id: str):
        # Needs to match key used by RedisChatMessageHistory
        # TODO we probably want to align this with the others
        return f"message_store:{user_id}:{thread_id}"

    def _dump(self, map: dict) -> dict:
        return {k: orjson.dumps(v) if v is not None else None for k, v in map.items()}

    def load(self, keys: list[str], values: list[bytes]) -> dict:
        return {
            k: orjson.loads(v) if v is not None else None for k, v in zip(keys, values)
        }

    def list_assistants(self, user_id: str):
        raise NotImplementedError("`list_assistants` is not implemented.")

    def list_public_assistants(self, assistant_ids: list[str]):
        raise NotImplementedError("`list_public_assistants` is not implemented.")

    def put_assistant(
        self,
        user_id: str,
        assistant_id: str,
        *,
        name: str,
        config: dict,
        public: bool = False,
    ):
        raise NotImplementedError("`put_assistant` is not implemented.")

    def list_threads(user_id: str):
        raise NotImplementedError("`list_threads` is not implemented.")

    def get_thread_messages(user_id: str, thread_id: str):
        raise NotImplementedError("`get_thread_messages` is not implemented.")

    def put_thread(user_id: str, thread_id: str, *, assistant_id: str, name: str):
        raise NotImplementedError("`put_thread` is not implemented.")
