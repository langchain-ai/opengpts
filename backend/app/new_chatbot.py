from langchain_core.messages import SystemMessage
from langgraph.graph import StateGraph, END
from typing import TypedDict, Annotated, Sequence
import operator
from langchain_core.messages import BaseMessage
from enum import Enum
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
    AZURE_OPENAI = "GPT 4 (Azure OpenAI)"
    CLAUDE2 = "Claude 2"
    BEDROCK_CLAUDE2 = "Claude 2 (Amazon Bedrock)"
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
    elif llm_type == LLMType.BEDROCK_CLAUDE2:
        llm = get_anthropic_llm(bedrock=True)
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
    messages: Annotated[Sequence[BaseMessage], operator.add]


DEFAULT_SYSTEM_MESSAGE = "You are a helpful assistant."


def _call_model(state, config):
    m = get_llm(config['configurable'].get('model', LLMType.GPT_35_TURBO))
    system_message = config['configurable'].get("system_message", DEFAULT_SYSTEM_MESSAGE)
    messages = [SystemMessage(content=system_message)] + state['messages']
    response = m.invoke(messages)
    return {"messages": [response]}

# Define a new graph
workflow = StateGraph(AgentState)
workflow.add_node("model", _call_model)
workflow.set_entry_point("model")
workflow.add_edge("model", END)

graph = workflow.compile()
