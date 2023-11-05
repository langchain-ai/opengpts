from typing import Any, Mapping, Optional, Sequence

from langchain.agents import AgentExecutor
from langchain.pydantic_v1 import BaseModel, Field
from langchain.tools.tavily_search import TavilySearchResults
from langchain.utilities.tavily_search import TavilySearchAPIWrapper
from langchain.schema.language_model import BaseLanguageModel
from langchain.schema.runnable import (
    RunnableBinding,
    ConfigurableField,
    ConfigurableFieldMultiOption,
    ConfigurableFieldSingleOption,
)
from langchain.schema.messages import AnyMessage
from langchain.tools import BaseTool

from . import agent_types_v1 as agent_types
from . import llms

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


DEFAULT_SYSTEM_MESSAGE = "You are a helpful assistant."


class ConfigurableAgent(RunnableBinding):
    tools: Sequence[BaseTool]
    llm: BaseLanguageModel
    agent: agent_types.GizmoAgentType
    system_message: str = DEFAULT_SYSTEM_MESSAGE

    def __init__(
        self,
        *,
        tools: Sequence[BaseTool],
        llm: BaseLanguageModel,
        agent: agent_types.GizmoAgentType = agent_types.GizmoAgentType.OPENAI_FUNCTIONS,
        system_message: str = DEFAULT_SYSTEM_MESSAGE,
        kwargs: Optional[Mapping[str, Any]] = None,
        config: Optional[Mapping[str, Any]] = None,
        **others: Any,
    ) -> None:
        others.pop("bound", None)
        if agent == agent_types.GizmoAgentType.OPENAI_FUNCTIONS:
            _agent = agent_types.get_openai_function_agent(llm, tools, system_message)
        elif agent == agent_types.GizmoAgentType.XML:
            _agent = agent_types.get_xml_agent(llm, tools, system_message)
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


class AgentInput(BaseModel):
    messages: Sequence[AnyMessage] = Field(..., extra={"widget": {"type": "chat"}})


class AgentOutput(BaseModel):
    messages: Sequence[AnyMessage] = Field(..., extra={"widget": {"type": "chat"}})
    output: str


agent = (
    ConfigurableAgent(
        llm=llms._get_llm_gpt_35_turbo(),
        agent=agent_types.GizmoAgentType.OPENAI_FUNCTIONS,
        tools=tools,
        system_message=DEFAULT_SYSTEM_MESSAGE,
    )
    .configurable_fields(
        agent=ConfigurableField(id="agent_type", name="agent_type"),
        system_message=ConfigurableField(id="system_message", name="system_message"),
        llm=ConfigurableFieldSingleOption(
            id="llm",
            options={
                "gpt-3.5-turbo": llms._get_llm_gpt_35_turbo(),
                "gpt-4": llms._get_llm_gpt_4(),
                "claude-2": llms._get_llm_claude2(),
                "zephyr": llms._get_llm_zephyr(),
            },
            default="gpt-3.5-turbo",
        ),
        tools=ConfigurableFieldMultiOption(
            id="tools",
            options={tool.name: tool for tool in tools},
            default=[],
        ),
    )
    .with_types(input_type=AgentInput, output_type=AgentOutput)
)
