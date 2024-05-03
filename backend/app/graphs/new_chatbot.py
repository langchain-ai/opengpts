from enum import Enum
from typing import TypedDict, Annotated, Sequence

from langchain_core.messages import BaseMessage, SystemMessage
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages

from app.llms import (
    get_anthropic_llm,
    get_google_llm,
    get_mixtral_fireworks,
    get_ollama_llm,
    get_openai_llm,
)


class LLMType(str, Enum):
    GPT_35_TURBO = "GPT 3.5 Turbo"
    GPT_4 = "GPT 4 Turbo"
    GPT_4O = "GPT 4o"
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
        llm = get_openai_llm(model="gpt-4-turbo")
    elif llm_type == LLMType.GPT_4O:
        llm = get_openai_llm(model="gpt-4o")
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


class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]


DEFAULT_SYSTEM_MESSAGE = "You are a helpful assistant."


def _call_model(state, config):
    m = get_llm(config["configurable"].get("type==chatbot/llm", LLMType.GPT_35_TURBO))
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
