from enum import Enum

from langchain.pydantic_v1 import BaseModel, Field
from langchain.tools import DuckDuckGoSearchRun
from langchain.tools.retriever import create_retriever_tool
from langchain.vectorstores.redis import RedisFilter

from gizmo_agent.ingest import vstore


class DDGInput(BaseModel):
    query: str = Field(description="search query to look up")


class PythonREPLInput(BaseModel):
    query: str = Field(description="python command to run")


RETRIEVER_DESCRIPTION = """Can be used to look up information that was uploaded to this assistant.
If the user is referencing particular files, that is often a good hint that information may be here."""


def get_retrieval_tool(user_id: str, assistant_id: str):
    return create_retriever_tool(
        vstore.as_retriever(
            filter=RedisFilter.tag("namespace") == f"{user_id}:{assistant_id}"
        ),
        "Retriever",
        RETRIEVER_DESCRIPTION,
    )


class AvailableTools(str, Enum):
    SEARCH = "Search"
    RETRIEVAL = "Retrieval"


TOOLS = {
    "Search": DuckDuckGoSearchRun(args_schema=DDGInput),
}

TOOL_OPTIONS = {e.value: e.value for e in AvailableTools}
