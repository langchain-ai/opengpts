from langchain.tools import DuckDuckGoSearchRun
from langchain.tools.tavily_search import TavilySearchResults
from langchain.utilities.tavily_search import TavilySearchAPIWrapper
from langchain_experimental.tools import PythonREPLTool
from langchain.pydantic_v1 import BaseModel, Field


class DDGInput(BaseModel):
    query: str = Field(description="search query to look up")

class PythonREPLInput(BaseModel):
    query: str = Field(description="python command to run")


TOOLS = [
    DuckDuckGoSearchRun(args_schema=DDGInput),
    TavilySearchResults(api_wrapper=TavilySearchAPIWrapper()),
    # PythonREPLTool(args_schema=PythonREPLInput),
]

TOOL_OPTIONS = {tool.name: tool for tool in TOOLS}
