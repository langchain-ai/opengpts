import os

from agent_executor import AgentExecutor
from agent_executor.history import RunnableWithMessageHistory
from langchain.pydantic_v1 import BaseModel, Field

from langchain.schema.messages import AnyMessage


from typing import Any, Mapping, Optional, Sequence

from langchain.schema.runnable import (
    RunnableBinding,
    ConfigurableField,
    ConfigurableFieldMultiOption,
)
from langchain.tools import BaseTool
from gizmo_agent.agent_types import (
    GizmoAgentType,
    get_xml_agent,
    get_openai_function_agent,
)
from gizmo_agent.tools import AvailableTools, TOOLS, TOOL_OPTIONS, get_retrieval_tool
from functools import partial

from langchain.prompts.chat import SystemMessagePromptTemplate, MessagesPlaceholder
from langchain.chat_models.openai import ChatOpenAI
from langchain.schema.output_parser import StrOutputParser
from langchain.memory.chat_message_histories import SQLChatMessageHistory
from langchain.memory import RedisChatMessageHistory


DEFAULT_SYSTEM_MESSAGE = "You are a helpful assistant."

from permchain import Channel, Pregel
from permchain.channels import Topic, LastValue
from langchain.chat_models import ChatOpenAI
from langchain.schema.agent import AgentAction, AgentFinish, AgentActionMessageLog
from langchain.schema.messages import AIMessage, FunctionMessage, HumanMessage, AnyMessage
import json
from langchain.tools import DuckDuckGoSearchRun
from langchain.pydantic_v1 import BaseModel, Field
from langchain.tools.render import format_tool_to_openai_function
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.agents.output_parsers import OpenAIFunctionsAgentOutputParser


def route_agent_action(output):
    if isinstance(output, AgentAction):
        if isinstance(output, AgentActionMessageLog):
            msgs = output.message_log

        else:
            msgs = [AIMessage(content=output.log)]

        return Channel.write_to(
            messages=lambda x: msgs,
            tool=lambda x: output
        )

    else:
        return Channel.write_to(
            messages=lambda x: AIMessage(content=output.return_values['output'])
        )


def _create_function_message(
        agent_action: AgentAction, observation: str
) -> FunctionMessage:
    if not isinstance(observation, str):
        try:
            content = json.dumps(observation, ensure_ascii=False)
        except Exception:
            content = str(observation)
    else:
        content = observation
    return FunctionMessage(
        name=agent_action.tool,
        content=content,
    )


def _load_messages(_input, config):
    print("hi")
    hist = config["configurable"]["message_history"]
    return Channel.write_to(
        messages=lambda x: hist.messages.copy() + [_input["human"]],
        assistant=lambda x: True
    )


class ConfigurableAgent(RunnableBinding):
    tools: Sequence[str]
    agent: GizmoAgentType
    system_message: str = DEFAULT_SYSTEM_MESSAGE
    assistant_id: Optional[str] = None

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
                    raise ValueError("assistant_id must be provided if Retrieval tool is used")
                _tools.append(get_retrieval_tool(assistant_id))
            else:
                _tools.append(TOOLS[_tool])
        if agent == GizmoAgentType.GPT_35_TURBO:
            _agent = get_openai_function_agent(_tools, system_message)
        elif agent == GizmoAgentType.GPT_35_TURBO:
            _agent = get_openai_function_agent(_tools, system_message, gpt_4=True)
        # elif agent == GizmoAgentType.AZURE_OPENAI:
        #     _agent = get_openai_function_agent(tools, system_message, azure=True)
        elif agent == GizmoAgentType.CLAUDE2:
            _agent = get_xml_agent(_tools, system_message)
        else:
            raise ValueError("Unexpected agent type")

        tool_map = {
            t.name: t for t in _tools
        }

        def run_logic(agent_action):
            tool = tool_map[agent_action.tool]
            observation = tool.run(agent_action.tool_input)
            return _create_function_message(agent_action, observation)

        tool_logic = (
                Channel.subscribe_to("tool")
                | run_logic
                | Channel.write_to(
            messages=lambda x: x,
            assistant=lambda x: True
        )
        )

        agent_logic = (
                Channel.subscribe_to(["assistant"]).join(['messages'])
                | _agent
                | route_agent_action

        )

        invoke_logic = Channel.subscribe_to(['human']) | _load_messages

        app = Pregel(
            chains={
                "invoke_logic": invoke_logic,
                "agent_logic": agent_logic,
                "tool_logic": tool_logic
            },
            channels={
                "messages": Topic(AnyMessage, accumulate=True),
                "assistant": LastValue(bool),
                "tool": LastValue(AnyMessage),
            },
            input=["human"],
            output=["messages"],
            debug=True,
        )
        super().__init__(
            tools=tools,
            agent=agent,
            system_message=system_message,
            bound=app,
            kwargs=kwargs or {},
            config=config or {},
        )


class AgentInput(BaseModel):
    input: AnyMessage


class AgentOutput(BaseModel):
    messages: Sequence[AnyMessage] = Field(..., extra={"widget": {"type": "chat"}})
    output: str


agent = ConfigurableAgent(
    agent=GizmoAgentType.GPT_35_TURBO,
    tools=[],
    system_message=DEFAULT_SYSTEM_MESSAGE,
    assistant_id=None,
).configurable_fields(
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
agent = RunnableWithMessageHistory(
    agent,
    # first arg should be a function that
    # - accepts a single arg "session_id"
    # - returns a BaseChatMessageHistory instance
    partial(RedisChatMessageHistory, url=os.environ["REDIS_URL"]),
    input_key="human",
    output_key="messages",
    history_key="messages",
).with_types(input_type=AgentInput, output_type=AgentOutput)

if __name__ == "__main__":
    import asyncio
    from langchain.schema.messages import HumanMessage

    async def run():
        print(agent.invoke(
            {"human": HumanMessage(content="whats my name")},
            config={"configurable": {"session_id": "test1"}},))
        # async for m in agent.astream_log(
        #     {"input": HumanMessage(content="whats my name")},
        #     config={"configurable": {"session_id": "test1"}},
        # ):
        #     print(m)

    asyncio.run(run())
