from typing import Any, get_args

from langchain_core.messages import (
    AnyMessage,
    FunctionMessage,
    MessageLikeRepresentation,
    ToolMessage,
)
from langgraph.graph.message import Messages, add_messages


class LiberalFunctionMessage(FunctionMessage):
    content: Any


class LiberalToolMessage(ToolMessage):
    content: Any


def _convert_pydantic_dict_to_message(
    data: MessageLikeRepresentation
) -> MessageLikeRepresentation:
    if (
        isinstance(data, dict)
        and "content" in data
        and isinstance(data.get("type"), str)
    ):
        for cls in get_args(AnyMessage):
            if data["type"] == cls(content="").type:
                return cls(**data)
    return data


def add_messages_liberal(left: Messages, right: Messages):
    # coerce to list
    if not isinstance(left, list):
        left = [left]
    if not isinstance(right, list):
        right = [right]
    return add_messages(
        [_convert_pydantic_dict_to_message(m) for m in left],
        [_convert_pydantic_dict_to_message(m) for m in right],
    )
