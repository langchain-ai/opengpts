import math
from typing import Any, Dict, Optional, Sequence, Union
from uuid import UUID

from anyio import create_memory_object_stream
from langchain.callbacks.base import BaseCallbackHandler
from langchain.schema.messages import (
    AIMessage,
    AIMessageChunk,
    BaseMessage,
    BaseMessageChunk,
    ChatMessage,
    ChatMessageChunk,
    FunctionMessage,
    FunctionMessageChunk,
    HumanMessage,
    HumanMessageChunk,
)
from langchain.schema.output import ChatGenerationChunk, GenerationChunk


class StreamMessagesHandler(BaseCallbackHandler):
    def __init__(self, messages: Sequence[BaseMessage]) -> None:
        self.messages = messages
        self.output: Dict[UUID, ChatGenerationChunk] = {}
        send_stream, receive_stream = create_memory_object_stream(math.inf)
        self.send_stream = send_stream
        self.receive_stream = receive_stream

    def on_llm_new_token(
        self,
        token: str,
        *,
        chunk: Optional[Union[GenerationChunk, ChatGenerationChunk]] = None,
        run_id: UUID,
        **kwargs: Any,
    ) -> Any:
        # If this is being called for a non-Chat Model run, convert to AIMessage
        if chunk is None:
            chunk = ChatGenerationChunk(message=AIMessageChunk(content=token))
        # If we get something we don't know how to handle, ignore it
        if not (
            isinstance(chunk, ChatGenerationChunk)
            or isinstance(chunk, BaseMessageChunk)
        ):
            return
        # Convert messages to ChatGenerationChunks (workaround for old langchahin)
        if isinstance(chunk, BaseMessageChunk):
            chunk = ChatGenerationChunk(message=chunk)
        # Accumulate the output (ChatGenerationChunk implements __add__)
        if not self.output.get(run_id):
            self.output[run_id] = chunk
        else:
            self.output[run_id] += chunk
        # Send the messages to the stream
        self.send_stream.send_nowait(
            {
                "messages": (
                    self.messages
                    + [
                        map_chunk_to_msg(chunk.message)
                        for chunk in self.output.values()
                    ]
                )
            }
        )


def map_chunk_to_msg(chunk: BaseMessageChunk) -> BaseMessage:
    if not isinstance(chunk, BaseMessageChunk):
        return chunk
    args = {k: v for k, v in chunk.__dict__.items() if k != "type"}
    if isinstance(chunk, HumanMessageChunk):
        return HumanMessage(**args)
    elif isinstance(chunk, AIMessageChunk):
        return AIMessage(**args)
    elif isinstance(chunk, FunctionMessageChunk):
        return FunctionMessage(**args)
    elif isinstance(chunk, ChatMessageChunk):
        return ChatMessage(**args)
    else:
        raise ValueError(f"Unknown chunk type: {chunk}")
