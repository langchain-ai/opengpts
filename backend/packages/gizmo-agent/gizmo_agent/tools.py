import os
from langchain.tools import DuckDuckGoSearchRun
from langchain_experimental.tools import PythonREPLTool
from langchain.pydantic_v1 import BaseModel, Field
from langchain.tools import BearlyInterpreterTool



class DDGInput(BaseModel):
    query: str = Field(description="search query to look up")


class PythonREPLInput(BaseModel):
    query: str = Field(description="python command to run")


bearly_tool = BearlyInterpreterTool(api_key=os.environ["BEARLY_API_KEY"])


TOOLS = [
    DuckDuckGoSearchRun(args_schema=DDGInput),
    PythonREPLTool(args_schema=PythonREPLInput),
    bearly_tool.as_tool()
]

TOOL_OPTIONS = {tool.name: tool for tool in TOOLS}
