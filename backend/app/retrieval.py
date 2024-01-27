import json

from langchain_core.language_models.base import LanguageModelLike
from langchain_core.messages import (
    SystemMessage,
    HumanMessage,
    AIMessage,
    FunctionMessage,
)
from langchain_core.runnables import chain
from langchain_core.retrievers import BaseRetriever
from langgraph.checkpoint import BaseCheckpointSaver
from langgraph.graph import END
from langgraph.graph.message import MessageGraph
from langchain_core.prompts import PromptTemplate


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


@chain
def get_search_query(llm, messages):
    convo = []
    for m in messages:
        if isinstance(m, AIMessage):
            if "function_call" not in m.additional_kwargs:
                convo.append(f"AI: {m.content}")
        if isinstance(m, HumanMessage):
            convo.append(f"Human: {m.content}")
    conversation = "\n".join(convo)
    prompt = search_prompt.invoke({"conversation": conversation})
    response = llm.invoke(prompt)
    return response.content


def get_retrieval_executor(
    llm: LanguageModelLike,
    retriever: BaseRetriever,
    system_message: str,
    checkpoint: BaseCheckpointSaver,
):
    def _get_messages(messages):
        chat_history = []
        for m in messages:
            if isinstance(m, AIMessage):
                if "function_call" not in m.additional_kwargs:
                    chat_history.append(m)
            if isinstance(m, HumanMessage):
                chat_history.append(m)
        content = messages[-1].content
        return [
            SystemMessage(
                content=response_prompt_template.format(
                    instructions=system_message, context=content
                )
            )
        ] + chat_history

    def invoke_retrieval(messages):
        if len(messages) == 1:
            human_input = messages[-1].content
            return AIMessage(
                content="",
                additional_kwargs={
                    "function_call": {
                        "name": "retrieval",
                        "arguments": json.dumps({"query": human_input}),
                    }
                },
            )
        else:
            search_query = get_search_query.invoke({"llm": llm, "messages": messages})
            return AIMessage(
                content="",
                additional_kwargs={
                    "function_call": {
                        "name": "retrieval",
                        "arguments": json.dumps({"query": search_query}),
                    }
                },
            )

    def retrieve(messages):
        params = messages[-1].additional_kwargs["function_call"]
        query = json.loads(params["arguments"])["query"]
        response = retriever.invoke(query)
        content = "\n".join([d.page_content for d in response])
        return FunctionMessage(name="retrieval", content=content)

    response = _get_messages | llm

    workflow = MessageGraph()
    workflow.add_node("invoke_retrieval", invoke_retrieval)
    workflow.add_node("retrieve", retrieve)
    workflow.add_node("response", response)
    workflow.set_entry_point("invoke_retrieval")
    workflow.add_edge("invoke_retrieval", "retrieve")
    workflow.add_edge("retrieve", "response")
    workflow.add_edge("response", END)
    app = workflow.compile(checkpointer=checkpoint)
    return app
