import json

from permchain import Channel, Pregel
from permchain.channels import Topic
from langchain.schema.runnable import (
    Runnable,
    RunnableConfig,
    RunnableLambda,
    RunnablePassthrough,
)
from langchain.schema.agent import AgentAction, AgentFinish, AgentActionMessageLog
from langchain.schema.messages import AIMessage, FunctionMessage, AnyMessage
from langchain.tools import BaseTool


def _create_agent_message(
    output: AgentAction | AgentFinish
) -> list[AnyMessage] | AnyMessage:
    if isinstance(output, AgentAction):
        if isinstance(output, AgentActionMessageLog):
            output.message_log[-1].additional_kwargs["agent"] = output
            return output.message_log
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


def run_tool(
    messages: list[AnyMessage], config: RunnableConfig, *, tools: dict[str, BaseTool]
) -> FunctionMessage:
    action: AgentAction = messages[-1].additional_kwargs["agent"]
    tool = tools[action.tool]
    result = tool.invoke(action.tool_input, config)
    return _create_function_message(action, result)


async def arun_tool(
    messages: list[AnyMessage], config: RunnableConfig, *, tools: dict[str, BaseTool]
) -> FunctionMessage:
    action: AgentAction = messages[-1].additional_kwargs["agent"]
    tool = tools[action.tool]
    result = await tool.ainvoke(action.tool_input, config)
    return _create_function_message(action, result)


def get_agent_executor(
    tools: list[BaseTool],
    agent: Runnable[dict[str, list[AnyMessage]], AgentAction | AgentFinish],
) -> Pregel:
    tool_map = {tool.name: tool for tool in tools}
    tool_lambda = RunnableLambda(run_tool, arun_tool).bind(tools=tool_map)

    tool_chain = tool_lambda | Channel.write_to("messages")
    agent_chain = (
        {"messages": RunnablePassthrough()}
        | agent
        | _create_agent_message
        | Channel.write_to("messages")
    )

    def route_last_message(messages: list[AnyMessage]) -> Runnable:
        message = messages[-1]
        if isinstance(message, AIMessage):
            if isinstance(message.additional_kwargs.get("agent"), AgentAction):
                return tool_chain
            elif isinstance(message.additional_kwargs.get("agent"), AgentFinish):
                return RunnablePassthrough()
        else:
            return agent_chain

    executor = Channel.subscribe_to("messages") | route_last_message

    # TODO add agent stop message

    return Pregel(
        chains={"executor": executor},
        channels={"messages": Topic(AnyMessage, accumulate=True)},
        input=["messages"],
        output=["messages"],
    )
