from typing import Annotated, List

from langchain_core.language_models.base import LanguageModelLike
from langchain_core.messages import BaseMessage, SystemMessage
from langgraph.checkpoint import BaseCheckpointSaver
from langgraph.graph import END
from langgraph.graph.message import add_messages
from langgraph.graph.state import StateGraph


def get_chatbot_executor(
    llm: LanguageModelLike,
    system_message: str,
    checkpoint: BaseCheckpointSaver,
):
    def _get_messages(messages):
        return [SystemMessage(content=system_message)] + messages

    chatbot = _get_messages | llm

    workflow = StateGraph(Annotated[List[BaseMessage], add_messages])
    workflow.add_node("chatbot", chatbot)
    workflow.set_entry_point("chatbot")
    workflow.add_edge("chatbot", END)
    app = workflow.compile(checkpointer=checkpoint)
    return app
