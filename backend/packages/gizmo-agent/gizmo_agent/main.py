from typing import List, Tuple

from langchain.agents import AgentExecutor
from langchain.agents.format_scratchpad import format_to_openai_functions
from langchain.agents.output_parsers import OpenAIFunctionsAgentOutputParser
from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.pydantic_v1 import BaseModel, Field
from langchain.tools.tavily_search import TavilySearchResults
from langchain.utilities.tavily_search import TavilySearchAPIWrapper

# Create the tool
search = TavilySearchAPIWrapper()
description = """"A search engine optimized for comprehensive, accurate, \
and trusted results. Useful for when you need to answer questions \
about current events or about recent information. \
Input should be a search query. \
If the user is asking about something that you don't know about, \
you should probably use this tool to see if that can provide any information."""
tavily_tool = TavilySearchResults(api_wrapper=search, description=description)

tools = [tavily_tool]

from pprint import pprint
from typing import Any, Mapping, Optional, Sequence

from langchain.agents import initialize_agent, AgentType
from langchain.callbacks.base import BaseCallbackManager
from langchain.chains import LLMMathChain
from langchain.chat_models.openai import ChatOpenAI
from langchain.schema.language_model import BaseLanguageModel
from langchain.schema.runnable import (
    RunnableBinding,
    ConfigurableField,
    ConfigurableFieldMultiOption,
    ConfigurableFieldSingleOption,
)
from langchain.tools import BaseTool, Tool
from gizmo_agent.agent_types_v1 import GizmoAgentType, get_xml_agent, get_openai_function_agent
from gizmo_agent.llms import LLM_OPTIONS
from gizmo_agent.tools import TOOL_OPTIONS

DEFAULT_SYSTEM_MESSAGE = "You are a helpful assistant."

class ConfigurableAgent(RunnableBinding):
    tools: Sequence[BaseTool]
    llm: BaseLanguageModel
    agent: GizmoAgentType
    system_message: str = DEFAULT_SYSTEM_MESSAGE

    def __init__(
        self,
        *,
        tools: Sequence[BaseTool],
        llm: BaseLanguageModel,
        agent: GizmoAgentType = GizmoAgentType.OPENAI_FUNCTIONS,
        system_message: str = DEFAULT_SYSTEM_MESSAGE,
        kwargs: Optional[Mapping[str, Any]] = None,
        config: Optional[Mapping[str, Any]] = None,
        **others: Any,
    ) -> None:
        others.pop("bound", None)
        if agent == GizmoAgentType.OPENAI_FUNCTIONS:
            _agent = get_openai_function_agent(llm, tools, system_message)
        elif agent == GizmoAgentType.XML:
            _agent = get_xml_agent(llm, tools, system_message)
        else:
            raise ValueError("Unexpected agent type")
        agent_executor = AgentExecutor(
            agent=_agent,
            tools=tools,
            handle_parsing_errors=True,
            max_iterations=10,

        )
        super().__init__(
            tools=tools,
            llm=llm,
            agent=agent,
            system_message=system_message,
            bound=agent_executor,
            kwargs=kwargs or {},
            config=config or {},
        )



from langchain.schema.messages import BaseMessage, HumanMessage
from langchain.load import load
from typing import Sequence
class AgentInput(BaseModel):
    messages: List[BaseMessage] = Field(..., extra={"widget": {"type": "chat"}})

class AgentOutput(BaseModel):
    output: str


agent = ConfigurableAgent(
    llm=LLM_OPTIONS["claude-2"],
    agent=GizmoAgentType.XML,
    tools=list(TOOL_OPTIONS.values()),
    system_message=DEFAULT_SYSTEM_MESSAGE,
).configurable_fields(

    agent=ConfigurableField(id="agent_type", name="agent_type"),
    system_message=ConfigurableField(id="system_message", name="system_message"),
    llm=ConfigurableFieldSingleOption(
        id="llm",
        options=LLM_OPTIONS,
        default="zephyr-ollama",
    ),
    tools=ConfigurableFieldMultiOption(
        id="tools",
        options=TOOL_OPTIONS,
        default=list(TOOL_OPTIONS.keys()),
    ),
)#.with_types(input_type=AgentInput)

print(agent.invoke({"messages": [HumanMessage(content="what is the weather in SF?")]}))
