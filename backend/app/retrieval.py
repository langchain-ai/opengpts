import operator
from typing import Annotated, List, Sequence, TypedDict
from uuid import uuid4

from langchain_core.language_models.base import LanguageModelLike
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_core.prompts import PromptTemplate
from langchain_core.retrievers import BaseRetriever
from langchain_core.runnables import chain
from langgraph.checkpoint import BaseCheckpointSaver
from langgraph.graph import END
from langgraph.graph.state import StateGraph

from app.message_types import LiberalToolMessage, add_messages_liberal

search_prompt = PromptTemplate.from_template(
    """Given the conversation below, come up with a search query to look up.

This search query can be either a few words or question

Return ONLY this search query, nothing more.

>>> Conversation:
{conversation}
>>> END OF CONVERSATION

Remember, return ONLY the search query that will help you when formulating a response to the above conversation."""
)


response_prompt_template = """{instructions}

Respond to the user using ONLY the context provided below. Do not make anything up.

{context}"""


def get_retrieval_executor(
    llm: LanguageModelLike,
    retriever: BaseRetriever,
    system_message: str,
    checkpoint: BaseCheckpointSaver,
):
    class AgentState(TypedDict):
        messages: Annotated[List[BaseMessage], add_messages_liberal]
        msg_count: Annotated[int, operator.add]

    def _get_messages(messages):
        chat_history = []
        for m in messages:
            if isinstance(m, AIMessage):
                if not m.tool_calls:
                    chat_history.append(m)
            if isinstance(m, HumanMessage):
                chat_history.append(m)
        response = messages[-1].content
        content = "\n".join([d.page_content for d in response])
        return [
            SystemMessage(
                content=response_prompt_template.format(
                    instructions=system_message, context=content
                )
            )
        ] + chat_history

    @chain
    async def get_search_query(messages: Sequence[BaseMessage]):
        convo = []
        for m in messages:
            if isinstance(m, AIMessage):
                if "function_call" not in m.additional_kwargs:
                    convo.append(f"AI: {m.content}")
            if isinstance(m, HumanMessage):
                convo.append(f"Human: {m.content}")
        conversation = "\n".join(convo)
        prompt = await search_prompt.ainvoke({"conversation": conversation})
        response = await llm.ainvoke(prompt, {"tags": ["nostream"]})
        return response

    async def invoke_retrieval(state: AgentState):
        messages = state["messages"]
        if len(messages) == 1:
            human_input = messages[-1]["content"]
            return {
                "messages": [
                    AIMessage(
                        content="",
                        tool_calls=[
                            {
                                "id": uuid4().hex,
                                "name": "retrieval",
                                "args": {"query": human_input},
                            }
                        ],
                    )
                ]
            }
        else:
            search_query = await get_search_query.ainvoke(messages)
            return {
                "messages": [
                    AIMessage(
                        id=search_query.id,
                        content="",
                        tool_calls=[
                            {
                                "id": uuid4().hex,
                                "name": "retrieval",
                                "args": {"query": search_query.content},
                            }
                        ],
                    )
                ]
            }

    async def retrieve(state: AgentState):
        messages = state["messages"]
        params = messages[-1].tool_calls[0]
        query = params["args"]["query"]
        response = await retriever.ainvoke(query)
        msg = LiberalToolMessage(
            name="retrieval", content=response, tool_call_id=params["id"]
        )
        return {"messages": [msg], "msg_count": 1}

    def call_model(state: AgentState):
        messages = state["messages"]
        response = llm.invoke(_get_messages(messages))
        return {"messages": [response], "msg_count": 1}

    workflow = StateGraph(AgentState)
    workflow.add_node("invoke_retrieval", invoke_retrieval)
    workflow.add_node("retrieve", retrieve)
    workflow.add_node("response", call_model)
    workflow.set_entry_point("invoke_retrieval")
    workflow.add_edge("invoke_retrieval", "retrieve")
    workflow.add_edge("retrieve", "response")
    workflow.add_edge("response", END)
    app = workflow.compile(checkpointer=checkpoint)
    return app
