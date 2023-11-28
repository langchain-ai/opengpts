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
