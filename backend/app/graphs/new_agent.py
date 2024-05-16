from enum import Enum
from typing import cast

from langchain_core.messages import (
    AIMessage,
    FunctionMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
)
from typing import TypedDict, Annotated

from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_core.messages import AIMessage, AnyMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.managed.few_shot import FewShotExamples
from langgraph.prebuilt import ToolNode
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolExecutor, ToolInvocation

from app.message_types import LiberalToolMessage
from app.llms import (
    get_anthropic_llm,
    get_google_llm,
    get_mixtral_fireworks,
    get_ollama_llm,
    get_openai_llm,
)
from app.tools import RETRIEVAL_DESCRIPTION, AvailableTools, TOOLS, get_retrieval_tool

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

class LLMType(str, Enum):
    GPT_35_TURBO = "GPT 3.5 Turbo"
    GPT_4 = "GPT 4 Turbo"
    AZURE_OPENAI = "GPT 4 (Azure OpenAI)"
    CLAUDE2 = "Claude 2"
    GEMINI = "GEMINI"
    MIXTRAL = "Mixtral"
    OLLAMA = "Ollama"


def get_llm(
    llm_type: LLMType,
):
    if llm_type == LLMType.GPT_35_TURBO:
        llm = get_openai_llm()
    elif llm_type == LLMType.GPT_4:
        llm = get_openai_llm(gpt_4=True)
    elif llm_type == LLMType.AZURE_OPENAI:
        llm = get_openai_llm(azure=True)
    elif llm_type == LLMType.CLAUDE2:
        llm = get_anthropic_llm()
    elif llm_type == LLMType.GEMINI:
        llm = get_google_llm()
    elif llm_type == LLMType.MIXTRAL:
        llm = get_mixtral_fireworks()
    elif llm_type == LLMType.OLLAMA:
        llm = get_ollama_llm()
    else:
        raise ValueError
    return llm


async def _get_messages(messages, system_message, examples):
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

    if len(examples) > 0:
        _examples = "\n\n".join(
            [
                f"Example {i}: " + _render_messages(e["messages"])
                for i, e in enumerate(examples)
            ]
        )
        system_message = system_message + """ Below are some examples of interactions you had with users. \
These were good interactions where the final result they got was the desired one. As much as possible, you should learn from these interactions and mimic them in the future. \
Pay particularly close attention to when tools are called, and what the inputs are.!

{examples}

Assist the user as they require!""".format(
            examples=_examples
        )

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
    messages = state['messages']
    examples = state.get('examples', [])
    _config = config["configurable"]
    system_message = _config.get("type==agent/system_message", DEFAULT_SYSTEM_MESSAGE)
    llm = get_llm(_config.get("type==agent/agent_type", LLMType.GPT_35_TURBO))
    tools = get_tools(
        _config.get("type==agent/tools"),
        _config.get("assistant_id"),
        _config.get("thread_id"),
        _config.get("type==agent/retrieval_description"),
    )
    if tools:
        llm = llm.bind_tools(tools)
    messages = await _get_messages(messages, system_message, examples)
    response = llm.invoke(messages)

    # graph state is a dict, so return type must be dict
    return {"messages": [response]}


# Define the function that determines whether to continue or not
def should_continue(state):
    messages = state['messages']
    last_message = messages[-1]
    # If there is no function call, then we finish
    if not last_message.tool_calls:
        return "end"
    # Otherwise if there is, we continue
    else:
        return "continue"


# Define the function to execute tools
async def call_tool(state, config):
    messages = state['messages']
    _config = config["configurable"]
    tools = get_tools(
        _config.get("type==agent/tools"),
        _config.get("assistant_id"),
        _config.get("thread_id"),
        _config.get("type==agent/retrieval_description"),
    )

    tool_executor = ToolExecutor(tools)
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

    # graph state is a dict, so return type must be dict
    return {"messages": tool_messages}


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
