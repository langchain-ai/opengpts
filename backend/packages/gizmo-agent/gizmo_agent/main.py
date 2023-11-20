from typing import Any, Mapping, Optional, Sequence

from agent_executor.checkpoint import RedisCheckpoint
from agent_executor.permchain import get_agent_executor
from langchain.pydantic_v1 import BaseModel, Field
from langchain.schema.messages import AnyMessage
from langchain.schema.runnable import (
    ConfigurableField,
    ConfigurableFieldMultiOption,
    RunnableBinding,
)

from gizmo_agent.agent_types import (
    GizmoAgentType,
    get_openai_function_agent,
    get_xml_agent,
)
from gizmo_agent.tools import TOOL_OPTIONS, TOOLS, AvailableTools, get_retrieval_tool

DEFAULT_SYSTEM_MESSAGE = "You are a helpful assistant."


class ConfigurableAgent(RunnableBinding):
    tools: Sequence[str]
    agent: GizmoAgentType
    system_message: str = DEFAULT_SYSTEM_MESSAGE
    assistant_id: Optional[str] = None
    user_id: Optional[str] = None

    def __init__(
        self,
        *,
        tools: Sequence[str],
        agent: GizmoAgentType = GizmoAgentType.GPT_35_TURBO,
        system_message: str = DEFAULT_SYSTEM_MESSAGE,
        assistant_id: Optional[str] = None,
        kwargs: Optional[Mapping[str, Any]] = None,
        config: Optional[Mapping[str, Any]] = None,
        **others: Any,
    ) -> None:
        others.pop("bound", None)
        _tools = []
        for _tool in tools:
            if _tool == AvailableTools.RETRIEVAL:
                if assistant_id is None:
                    raise ValueError(
                        "assistant_id must be provided if Retrieval tool is used"
                    )
                _tools.append(get_retrieval_tool(assistant_id))
            else:
                _tools.append(TOOLS[_tool]())
        if agent == GizmoAgentType.GPT_35_TURBO:
            _agent = get_openai_function_agent(_tools, system_message)
        # elif agent == GizmoAgentType.GPT_4:
        #     _agent = get_openai_function_agent(_tools, system_message, gpt_4=True)
        elif agent == GizmoAgentType.AZURE_OPENAI:
            _agent = get_openai_function_agent(_tools, system_message, azure=True)
        elif agent == GizmoAgentType.CLAUDE2:
            _agent = get_xml_agent(_tools, system_message)
        elif agent == GizmoAgentType.BEDROCK_CLAUDE2:
            _agent = get_xml_agent(_tools, system_message, bedrock=True)
        else:
            raise ValueError("Unexpected agent type")
        agent_executor = get_agent_executor(
            tools=_tools, agent=_agent, checkpoint=RedisCheckpoint()
        ).with_config({"recursion_limit": 10})
        super().__init__(
            tools=tools,
            agent=agent,
            system_message=system_message,
            bound=agent_executor,
            kwargs=kwargs or {},
            config=config or {},
        )


class AgentInput(BaseModel):
    messages: Sequence[AnyMessage] = Field(default_factory=list)


class AgentOutput(BaseModel):
    messages: Sequence[AnyMessage] = Field(..., extra={"widget": {"type": "chat"}})


agent = (
    ConfigurableAgent(
        agent=GizmoAgentType.GPT_35_TURBO,
        tools=[],
        system_message=DEFAULT_SYSTEM_MESSAGE,
        assistant_id=None,
    )
    .configurable_fields(
        agent=ConfigurableField(id="agent_type", name="Agent Type"),
        system_message=ConfigurableField(id="system_message", name="System Message"),
        assistant_id=ConfigurableField(id="assistant_id", name="Assistant ID"),
        tools=ConfigurableFieldMultiOption(
            id="tools",
            name="Tools",
            options=TOOL_OPTIONS,
            default=[],
        ),
    )
    .with_types(input_type=AgentInput, output_type=AgentOutput)
)

if __name__ == "__main__":
    import asyncio

    from langchain.schema.messages import HumanMessage

    async def run():
        async for m in agent.astream_log(
            {"messages": HumanMessage(content="whats your name")},
            config={"configurable": {"user_id": "1", "thread_id": "test1"}},
        ):
            print(m)

    asyncio.run(run())
