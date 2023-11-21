import json
from operator import itemgetter
from typing import Sequence

from langchain.schema.agent import AgentAction, AgentActionMessageLog, AgentFinish
from langchain.schema.messages import (
    AnyMessage,
    AIMessage,
    AIMessageChunk,
    BaseMessage,
    BaseMessageChunk,
    ChatMessage,
    ChatMessageChunk,
    FunctionMessage,
    FunctionMessageChunk,
    HumanMessage,
    HumanMessageChunk,
)
from langchain.schema.runnable import (
    Runnable,
    RunnableConfig,
    RunnableLambda,
    RunnablePassthrough,
)
from langchain.tools import BaseTool
from permchain import Channel, Pregel, ReservedChannels
from permchain.channels import Topic, LastValue
from permchain.checkpoint.base import BaseCheckpointAdapter


def map_chunk_to_msg(chunk: BaseMessageChunk) -> BaseMessage:
    if not isinstance(chunk, BaseMessageChunk):
        return chunk
    args = {k: v for k, v in chunk.__dict__.items() if k != "type"}
    if isinstance(chunk, HumanMessageChunk):
        return HumanMessage(**args)
    elif isinstance(chunk, AIMessageChunk):
        return AIMessage(**args)
    elif isinstance(chunk, FunctionMessageChunk):
        return FunctionMessage(**args)
    elif isinstance(chunk, ChatMessageChunk):
        return ChatMessage(**args)
    else:
        raise ValueError(f"Unknown chunk type: {chunk}")


def _create_agent_message(
    output: AgentAction | AgentFinish
) -> list[AnyMessage] | AnyMessage:
    if isinstance(output, AgentAction):
        if isinstance(output, AgentActionMessageLog):
            output.message_log[-1].additional_kwargs["agent"] = output
            messages = [map_chunk_to_msg(m) for m in output.message_log]
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
    search,
    writer,
    checkpoint: BaseCheckpointAdapter,
) -> Pregel:

    search_chain = Channel.subscribe_to(["question"]) | search | Channel.write_to("research_summary")
    writer_chain = Channel.subscribe_to(["research_summary"]).join(['question']) | writer | Channel.write_to("draft")

    return Pregel(
        chains={"search": search_chain, "writer": writer_chain},
        channels={
            "question": LastValue(str),
            "research_summary": LastValue(str),
            "draft": LastValue(str),
        },
        input=["question"],
        output=["draft"],
        checkpoint=checkpoint,
    )