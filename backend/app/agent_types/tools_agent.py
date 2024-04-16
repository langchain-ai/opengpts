from typing import cast

from langchain.tools import BaseTool
from langchain_core.language_models.base import LanguageModelLike
from langchain_core.messages import (
    AIMessage,
    FunctionMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
)
from langgraph.checkpoint import BaseCheckpointSaver
from langgraph.graph import END
from langgraph.graph.message import MessageGraph
from langgraph.prebuilt import ToolExecutor, ToolInvocation

from app.message_types import LiberalToolMessage


def get_tools_agent_executor(
    tools: list[BaseTool],
    llm: LanguageModelLike,
    system_message: str,
    interrupt_before_action: bool,
    checkpoint: BaseCheckpointSaver,
):
    async def _get_messages(messages):
        msgs = []
        for m in messages:
            if isinstance(m, LiberalToolMessage):
                _dict = m.dict()
                _dict["content"] = str(_dict["content"])
                m_c = ToolMessage(**_dict)
                msgs.append(m_c)
            elif isinstance(m, FunctionMessage):
                # anthropic doesn't like function messages
                msgs.append(HumanMessage(content=str(m.content)))
            else:
                msgs.append(m)

        return [SystemMessage(content=system_message)] + msgs

    if tools:
        llm_with_tools = llm.bind_tools(tools)
    else:
        llm_with_tools = llm
    agent = _get_messages | llm_with_tools
    tool_executor = ToolExecutor(tools)

    # Define the function that determines whether to continue or not
    def should_continue(messages):
        last_message = messages[-1]
        # If there is no function call, then we finish
        if not last_message.tool_calls:
            return "end"
        # Otherwise if there is, we continue
        else:
            return "continue"

    # Define the function to execute tools
    async def call_tool(messages):
        actions: list[ToolInvocation] = []
        # Based on the continue condition
        # we know the last message involves a function call
        last_message = cast(AIMessage, messages[-1])
        for tool_call in last_message.tool_calls:
            # We construct a ToolInvocation from the function_call
            actions.append(
                ToolInvocation(
                    tool=tool_call["name"],
                    tool_input=tool_call["args"],
                )
            )
        # We call the tool_executor and get back a response
        responses = await tool_executor.abatch(actions)
        # We use the response to create a ToolMessage
        tool_messages = [
            LiberalToolMessage(
                tool_call_id=tool_call["id"],
                name=tool_call["name"],
                content=response,
            )
            for tool_call, response in zip(last_message.tool_calls, responses)
        ]
        return tool_messages

    workflow = MessageGraph()

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
    return workflow.compile(
        checkpointer=checkpoint,
        interrupt_before=["action"] if interrupt_before_action else None,
    )
