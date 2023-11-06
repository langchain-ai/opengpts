from agent_executor import AgentExecutor
from langchain.pydantic_v1 import BaseModel, Field

from langchain.schema.messages import AnyMessage


from typing import Any, Mapping, Optional, Sequence

from langchain.schema.language_model import BaseLanguageModel
from langchain.schema.runnable import (
    RunnableBinding,
    ConfigurableField,
    ConfigurableFieldMultiOption,
    ConfigurableFieldSingleOption,
)
from langchain.tools import BaseTool
from gizmo_agent.agent_types import (
    GizmoAgentType,
    get_xml_agent,
    get_openai_function_agent,
)
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


class AgentInput(BaseModel):
    messages: Sequence[AnyMessage] = Field(..., extra={"widget": {"type": "chat"}})


class AgentOutput(BaseModel):
    messages: Sequence[AnyMessage] = Field(..., extra={"widget": {"type": "chat"}})
    output: str


agent = (
    ConfigurableAgent(
        llm=LLM_OPTIONS["gpt-3.5-turbo"],
        agent=GizmoAgentType.OPENAI_FUNCTIONS,
        tools=list(TOOL_OPTIONS.values()),
        system_message=DEFAULT_SYSTEM_MESSAGE,
    )
    .configurable_fields(
        agent=ConfigurableField(id="agent_type", name="agent_type"),
        system_message=ConfigurableField(id="system_message", name="system_message"),
        llm=ConfigurableFieldSingleOption(
            id="llm",
            options=LLM_OPTIONS,
            default="gpt-3.5-turbo",
        ),
        tools=ConfigurableFieldMultiOption(
            id="tools",
            options=TOOL_OPTIONS,
            default=list(TOOL_OPTIONS.keys()),
        ),
    )
    .with_types(input_type=AgentInput, output_type=AgentOutput)
)
