from typing import TypedDict, Annotated

from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_core.messages import AIMessage, AnyMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.managed.few_shot import FewShotExamples
from langgraph.prebuilt import ToolNode


### TOOLS AND MODEL ###

tools = [TavilySearchResults(max_results=1)]
tool_node = ToolNode(tools)

model = ChatOpenAI(temperature=0)
model = model.bind_tools(tools)

### NODES ###

# Define the function that determines whether to continue or not
def should_continue(state):
    last_message = state["messages"][-1]
    # If there is no function call, then we finish
    if not last_message.tool_calls:
        return "end"
    # Otherwise if there is, we continue
    else:
        return "continue"

### GRAPH ###

class BaseState(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]
    examples: Annotated[list, FewShotExamples]


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


def _render_messages(ms):
    m_string = [_render_message(m) for m in ms]
    return "\n".join(m_string)


# Define a new graph
workflow = StateGraph(BaseState)

def _agent(state: BaseState):
    if len(state["examples"]) > 0:
        _examples = "\n\n".join(
            [
                f"Example {i}: " + _render_messages(e["messages"])
                for i, e in enumerate(state["examples"])
            ]
        )
        system_message = """You are a helpful assistant. Below are some examples of interactions you had with users. \
These were good interactions where the final result they got was the desired one. As much as possible, you should learn from these interactions and mimic them in the future. \
Pay particularly close attention to when tools are called, and what the inputs are.!

{examples}

Assist the user as they require!""".format(
            examples=_examples
        )

    else:
        system_message = """You are a helpful assistant"""
    output = model.invoke([SystemMessage(content=system_message)] + state["messages"])
    return {"messages": [output]}


# Define the two nodes we will cycle between
workflow.add_node("agent", _agent)
workflow.add_node("action", tool_node)

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

graph = workflow.compile(interrupt_before=["action"])