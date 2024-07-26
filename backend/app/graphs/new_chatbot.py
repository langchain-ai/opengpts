from enum import Enum
from typing import Annotated, Sequence, TypedDict

from langchain_core.messages import BaseMessage, SystemMessage
from langgraph.graph import END, StateGraph
from langgraph.graph.message import add_messages

from app.llms import LLMType, get_llm

class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]


DEFAULT_SYSTEM_MESSAGE = "You are a helpful assistant."


def _call_model(state, config):
    m = get_llm(config["configurable"].get("type==chatbot/llm_type", LLMType.GPT_4O_MINI))
    system_message = config["configurable"].get(
        "type==chatbot/system_message", DEFAULT_SYSTEM_MESSAGE
    )
    messages = [SystemMessage(content=system_message)] + state["messages"]
    response = m.invoke(messages)
    return {"messages": [response]}


# Define a new graph
workflow = StateGraph(AgentState)
workflow.add_node("model", _call_model)
workflow.set_entry_point("model")
workflow.add_edge("model", END)

graph = workflow.compile()
