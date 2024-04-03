import logging
from typing import AsyncIterator, Optional, Sequence, Union

import orjson
from langchain_core.messages import AnyMessage, BaseMessage, message_chunk_to_message
from langchain_core.runnables import Runnable, RunnableConfig
from langserve.serialization import WellKnownLCSerializer

logger = logging.getLogger(__name__)

MessagesStream = AsyncIterator[Union[list[AnyMessage], str]]


async def astream_messages(
    app: Runnable, input: Sequence[AnyMessage], config: RunnableConfig
) -> MessagesStream:
    """Stream messages from the runnable."""
    root_run_id: Optional[str] = None
    messages: dict[str, BaseMessage] = {}

    async for event in app.astream_events(
        input, config, version="v1", stream_mode="values"
    ):
        if event["event"] == "on_chain_start" and not root_run_id:
            root_run_id = event["run_id"]
            yield root_run_id
        elif event["event"] == "on_chain_stream" and event["run_id"] == root_run_id:
            new_messages: list[BaseMessage] = []
            for msg in event["data"]["chunk"]:
                if msg.id in messages and msg == messages[msg.id]:
                    continue
                else:
                    messages[msg.id] = msg
                    new_messages.append(msg)
            if new_messages:
                yield new_messages
        elif event["event"] == "on_chat_model_stream":
            message: BaseMessage = event["data"]["chunk"]
            if message.id not in messages:
                messages[message.id] = message
            else:
                messages[message.id] += message
            yield [messages[message.id]]


_serializer = WellKnownLCSerializer()


async def to_sse(messages_stream: MessagesStream) -> AsyncIterator[dict]:
    """Consume the stream into an EventSourceResponse"""
    try:
        async for chunk in messages_stream:
            # EventSourceResponse expects a string for data
            # so after serializing into bytes, we decode into utf-8
            # to get a string.
            if isinstance(chunk, str):
                yield {
                    "event": "metadata",
                    "data": orjson.dumps({"run_id": chunk}).decode(),
                }
            else:
                yield {
                    "event": "data",
                    "data": _serializer.dumps(
                        [message_chunk_to_message(msg) for msg in chunk]
                    ).decode(),
                }
    except Exception:
        logger.warn("error in stream", exc_info=True)
        yield {
            "event": "error",
            # Do not expose the error message to the client since
            # the message may contain sensitive information.
            # We'll add client side errors for validation as well.
            "data": orjson.dumps(
                {"status_code": 500, "message": "Internal Server Error"}
            ).decode(),
        }

    # Send an end event to signal the end of the stream
    yield {"event": "end"}
