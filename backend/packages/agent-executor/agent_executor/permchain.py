import json
from operator import itemgetter
from typing import Sequence

from langchain.schema.agent import AgentAction, AgentActionMessageLog, AgentFinish
from langchain.schema.messages import AIMessage, AnyMessage, FunctionMessage
from langchain.schema.runnable import (
    Runnable,
    RunnableConfig,
    RunnableLambda,
    RunnablePassthrough,
)
from langchain.tools import BaseTool
from permchain import Channel, Pregel, ReservedChannels
from permchain.channels import Topic
from permchain.checkpoint.base import BaseCheckpointAdapter


def _create_agent_message(
    output: AgentAction | AgentFinish
) -> list[AnyMessage] | AnyMessage:
    if isinstance(output, AgentAction):
        if isinstance(output, AgentActionMessageLog):
            output.message_log[-1].additional_kwargs["agent"] = output
            messages = output.message_log
            output.message_log = []  # avoid circular reference for json dumps
            return messages
        else:
            return AIMessage(
                content=output.log,
                additional_kwargs={"agent": output},
            )
    else:
        return AIMessage(
            content=output.return_values["output"],
            additional_kwargs={"agent": output},
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


def _run_tool(
    messages: list[AnyMessage], config: RunnableConfig, *, tools: dict[str, BaseTool]
) -> FunctionMessage:
    action: AgentAction = messages[-1].additional_kwargs["agent"]
    tool = tools[action.tool]
    result = tool.invoke(action.tool_input, config)
    return _create_function_message(action, result)


async def _arun_tool(
    messages: list[AnyMessage], config: RunnableConfig, *, tools: dict[str, BaseTool]
) -> FunctionMessage:
    action: AgentAction = messages[-1].additional_kwargs["agent"]
    tool = tools[action.tool]
    result = await tool.ainvoke(action.tool_input, config)
    return _create_function_message(action, result)


def get_agent_executor(
    tools: list[BaseTool],
    agent: Runnable[dict[str, list[AnyMessage]], AgentAction | AgentFinish],
    checkpoint: BaseCheckpointAdapter,
) -> Pregel:
    tool_map = {tool.name: tool for tool in tools}
    tool_lambda = RunnableLambda(_run_tool, _arun_tool).bind(tools=tool_map)

    tool_chain = itemgetter("messages") | tool_lambda | Channel.write_to("messages")
    agent_chain = agent | _create_agent_message | Channel.write_to("messages")

    def route_last_message(input: dict[str, bool | Sequence[AnyMessage]]) -> Runnable:
        if not input["messages"]:
            # no messages, do nothing
            return agent_chain

        message: AnyMessage = input["messages"][-1]
        if isinstance(message.additional_kwargs.get("agent"), AgentFinish):
            # finished, do nothing
            return RunnablePassthrough()

        if input[ReservedChannels.is_last_step]:
            # exhausted iterations without finishing, return stop message
            return Channel.write_to(
                messages=_create_agent_message(
                    AgentFinish(
                        {
                            "output": "Agent stopped due to iteration limit or time limit."
                        },
                        "",
                    )
                )
            )

        if isinstance(message.additional_kwargs.get("agent"), AgentAction):
            # agent action, run it
            return tool_chain

        # otherwise, run the agent
        return agent_chain

    executor = (
        Channel.subscribe_to(["messages"]).join([ReservedChannels.is_last_step])
        | route_last_message
    )

    return Pregel(
        chains={"executor": executor},
        channels={"messages": Topic(AnyMessage, accumulate=True)},
        input=["messages"],
        output=["messages"],
        checkpoint=checkpoint,
    )
