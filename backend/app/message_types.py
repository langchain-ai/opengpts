from typing import Any

from langchain_core.messages import FunctionMessage, ToolMessage
from langchain_core.load.load import ALL_SERIALIZABLE_MAPPINGS


class LiberalFunctionMessage(FunctionMessage):
    content: Any


class LiberalToolMessage(ToolMessage):
    content: Any


# Register for deserialization

ALL_SERIALIZABLE_MAPPINGS[
    ("langchain", "schema", "messages", "LiberalFunctionMessage")
] = ("app", "message_types", "LiberalFunctionMessage")

ALL_SERIALIZABLE_MAPPINGS[("langchain", "schema", "messages", "LiberalToolMessage")] = (
    "app",
    "message_types",
    "LiberalToolMessage",
)
