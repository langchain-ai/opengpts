from typing import Annotated, Any, Dict, TypedDict

from langchain_core.messages import (
    AIMessage,
    AnyMessage,
    FunctionMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
)
from langchain_core.runnables import RunnableConfig
from langgraph.graph import END, StateGraph
from langgraph.graph.message import Messages, add_messages
from langgraph.prebuilt import ToolNode

from app.llms import LLMType, get_llm
from app.message_types import LiberalToolMessage
from app.tools import RETRIEVAL_DESCRIPTION, TOOLS, AvailableTools, get_retrieval_tool


def filter_by_assistant_id(config: RunnableConfig) -> Dict[str, Any]:
    if "assistant_id" in config["configurable"]:
        return {"assistant_id": config["configurable"]["assistant_id"]}
    else:
        return {}


def custom_add_messages(left: Messages, right: Messages):
    combined_messages = add_messages(left, right)
    for message in combined_messages:
        # TODO: handle this correctly in ChatAnthropic.
        # this is needed to handle content blocks in AIMessageChunk when using
        # streaming with the graph. if we don't have that, all of the AIMessages
        # will have list of dicts in the content
        if (
            isinstance(message, AIMessage)
            and isinstance(message.content, list)
            and (
                text_content_blocks := [
                    content_block
                    for content_block in message.content
                    if content_block["type"] == "text"
                ]
            )
        ):
            message.content = "".join(
                content_block["text"] for content_block in text_content_blocks
            )

    return combined_messages


class BaseState(TypedDict):
    messages: Annotated[list[AnyMessage], custom_add_messages]


def _render_message(m):
    if isinstance(m, HumanMessage):
        return "Human: " + m.content
    elif isinstance(m, AIMessage):
        _m = "AI: " + m.content
        if len(m.tool_calls) > 0:
            _m += f" Tools: {m.tool_calls}"
        return _m
    elif isinstance(m, ToolMessage):
        return "Tool Result: ..."
    else:
        raise ValueError


def _get_messages(messages, system_message):
    msgs = []
    for m in messages:
        if isinstance(m, LiberalToolMessage):
            _dict = m.model_dump()
            _dict["content"] = str(_dict["content"])
            m_c = ToolMessage(**_dict)
            msgs.append(m_c)
        elif isinstance(m, FunctionMessage):
            # anthropic doesn't like function messages
            msgs.append(HumanMessage(content=str(m.content)))
        else:
            msgs.append(m)

    return [SystemMessage(content=system_message)] + msgs


DEFAULT_SYSTEM_MESSAGE = "You are a helpful assistant."


def get_tools(
    tools, assistant_id, thread_id, retrieval_description=RETRIEVAL_DESCRIPTION
):
    _tools = []
    for _tool in tools:
        if _tool["type"] == AvailableTools.RETRIEVAL:
            if assistant_id is None or thread_id is None:
                raise ValueError(
                    "Both assistant_id and thread_id must be provided if Retrieval tool is used"
                )
            _tools.append(
                get_retrieval_tool(assistant_id, thread_id, retrieval_description)
            )
        else:
            tool_config = _tool.get("config", {})
            _returned_tools = TOOLS[_tool["type"]](**tool_config)
            if isinstance(_returned_tools, list):
                _tools.extend(_returned_tools)
            else:
                _tools.append(_returned_tools)
    return _tools


async def agent(state, config):
    messages = state["messages"]
    _config = config["configurable"]
    system_message = _config.get("type==agent/system_message", DEFAULT_SYSTEM_MESSAGE)
    llm = get_llm(_config.get("type==agent/agent_type", LLMType.GPT_4O_MINI))
    tools = get_tools(
        _config.get("type==agent/tools"),
        _config.get("assistant_id"),
        _config.get("thread_id"),
        _config.get("type==agent/retrieval_description"),
    )
    if tools:
        llm = llm.bind_tools(tools)
    messages = _get_messages(messages, system_message)
    response = await llm.ainvoke(messages)

    # graph state is a dict, so return type must be dict
    return {"messages": [response]}


# Define the function that determines whether to continue or not
def should_continue(state):
    messages = state["messages"]
    last_message = messages[-1]
    # If there is no function call, then we finish
    if not last_message.tool_calls:
        return "end"
    # Otherwise if there is, we continue
    else:
        return "continue"


# Define the function to execute tools
async def call_tool(state, config):
    _config = config["configurable"]
    tools = get_tools(
        _config.get("type==agent/tools"),
        _config.get("assistant_id"),
        _config.get("thread_id"),
        _config.get("type==agent/retrieval_description"),
    )

    tool_node = ToolNode(tools)
    return await tool_node.ainvoke(state)


workflow = StateGraph(BaseState)

# Define the two nodes we will cycle between
workflow.add_node("agent", agent)
workflow.add_node("action", call_tool)

# Set the entrypoint as `agent`
# This means that this node is the first one called
workflow.set_entry_point("agent")

# We now add a conditional edge
workflow.add_conditional_edges(
    # First, we define the start node. We use `agent`.
    # This means these are the edges taken after the `agent` node is called.
    "agent",
    # Next, we pass in the function that will determine which node is called next.
    should_continue,
    # Finally we pass in a mapping.
    # The keys are strings, and the values are other nodes.
    # END is a special node marking that the graph should finish.
    # What will happen is we will call `should_continue`, and then the output of that
    # will be matched against the keys in this mapping.
    # Based on which one it matches, that node will then be called.
    {
        # If `tools`, then we call the tool node.
        "continue": "action",
        # Otherwise we finish.
        "end": END,
    },
)

# We now add a normal edge from `tools` to `agent`.
# This means that after `tools` is called, `agent` node is called next.
workflow.add_edge("action", "agent")

# Finally, we compile it!
# This compiles it into a LangChain Runnable,
# meaning you can use it as you would any other runnable
graph = workflow.compile()
