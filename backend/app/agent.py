import random
from enum import Enum
from typing import Any, Mapping, Optional, Sequence, Union

from langchain_core.messages import AnyMessage
from langchain_core.runnables import (
    ConfigurableField,
    RunnableBinding,
)
from langgraph.checkpoint import CheckpointAt
from langsmith import Client as LangSmithClient

from app.agent_types.google_agent import get_google_agent_executor
from app.agent_types.openai_agent import get_openai_agent_executor
from app.agent_types.xml_agent import get_xml_agent_executor
from app.chatbot import get_chatbot_executor
from app.checkpoint import PostgresCheckpoint
from app.llms import (
    get_anthropic_llm,
    get_google_llm,
    get_mixtral_fireworks,
    get_openai_llm,
)
from app.retrieval import get_retrieval_executor
from app.tools import (
    RETRIEVAL_DESCRIPTION,
    TOOLS,
    ActionServer,
    Arxiv,
    AvailableTools,
    Connery,
    DDGSearch,
    PressReleases,
    PubMed,
    Retrieval,
    SecFilings,
    Tavily,
    TavilyAnswer,
    Wikipedia,
    YouSearch,
    get_retrieval_tool,
    get_retriever,
)

Tool = Union[
    ActionServer,
    Connery,
    DDGSearch,
    Arxiv,
    YouSearch,
    SecFilings,
    PressReleases,
    PubMed,
    Wikipedia,
    Tavily,
    TavilyAnswer,
    Retrieval,
]


class AgentType(str, Enum):
    GPT_35_TURBO = "GPT 3.5 Turbo"
    # GPT_4 = "GPT 4 Turbo"
    # AZURE_OPENAI = "GPT 4 (Azure OpenAI)"
    # CLAUDE2 = "Claude 2"
    # BEDROCK_CLAUDE2 = "Claude 2 (Amazon Bedrock)"
    # GEMINI = "GEMINI"


DEFAULT_SYSTEM_MESSAGE = "You are a helpful assistant."

CHECKPOINTER = PostgresCheckpoint(at=CheckpointAt.END_OF_STEP)
LANGSMITH_CLIENT = LangSmithClient()


def _format_example(e):
    return f"""<input>
{e.inputs['input'][0]['content']}
</input>
<output>
{e.outputs['output']['content']}
</output>"""


def _format_trajectory(e):
    s = "<trajectory>"
    for i in e.inputs["input"]:
        s += f"\n{i['type']}: {i['content']}\n"
    s += f"\nFinal Answer: {e.outputs['output']['content']}\n"
    s += "</trajectory>"
    return s


def _get_learnings(examples):
    learnings = []
    for e in examples:
        for i in e.inputs["input"][1:]:
            print(i)
            if i["type"] == "human":
                learnings.append(i["content"])
    return learnings


def _format_example_agent(e):
    return f"""<trajectory>
{e.inputs['input'] +[ e.outputs['output']]}
</trajectory>"""


def _format_example_agent1(e):
    new_messages = []
    for o in e.outputs["output"][1:][::-1]:
        if o["type"] == "human":
            break
        new_messages.append(o)
    return f"""<trajectory>
{[e.outputs['output'][0]] + new_messages[::-1]}
</trajectory>"""


def _get_agent_examples(examples):
    es = {}
    for e in examples:
        key = e.inputs["input"][0]["content"]
        if key in es:
            curr_val = len(es[key].inputs["input"])
            new_val = len(e.inputs["input"])
            # Take the longer example
            if new_val > curr_val:
                es[key] = e
        else:
            es[key] = e
    return list(es.values())


def few_shot_examples(assistant_id: str, agent: bool = False):
    if LANGSMITH_CLIENT.has_dataset(dataset_name=assistant_id):
        # TODO: Update to randomize
        examples = list(LANGSMITH_CLIENT.list_examples(dataset_name=assistant_id))
        if not examples:
            return ""
        if agent:
            # examples = _get_agent_examples(examples)
            # examples = random.sample(examples, min(len(examples), 10))
            # e_str = "\n".join([_format_example_agent(e) for e in examples])
            examples = random.sample(examples, min(len(examples), 10))
            e_str = "\n".join([_format_example_agent1(e) for e in examples])
        else:
            examples = random.sample(examples, min(len(examples), 10))
            e_str = "\n".join([_format_example(e) for e in examples])
            learnings = _get_learnings(examples)
            e_str += (
                "\n\nHere are some of the comments that lead to these examples. Keep these comments in mind as you generate a new tweet!"
                + "\n".join(learnings)
            )
            # e_str = "\n".join([_format_trajectory(e) for e in examples])
        #         return f"""
        #
        # Here are some examples of good inputs and outputs. Use these to guide and shape the style of what your new response should look like:
        # {e_str}
        # """
        return f"""

Here are some previous interactions with a user trying to accomplish a similar task. You should assumed that the final result in all scenarios is the desired one, and any previous steps were wrong in some way, and the human then tried to improve upon them in specific ways. Learn from these previous interactions and do not repeat previous mistakes!
{e_str}
"""


def get_agent_executor(
    tools: list,
    agent: AgentType,
    system_message: str,
    interrupt_before_action: bool,
    assistant_id: Optional[str] = None,
):
    if assistant_id is not None:
        system_message += few_shot_examples(assistant_id, agent=True)
    if agent == AgentType.GPT_35_TURBO:
        llm = get_openai_llm()
        return get_openai_agent_executor(
            tools, llm, system_message, interrupt_before_action, CHECKPOINTER
        )
    elif agent == AgentType.GPT_4:
        llm = get_openai_llm(gpt_4=True)
        return get_openai_agent_executor(
            tools, llm, system_message, interrupt_before_action, CHECKPOINTER
        )
    elif agent == AgentType.AZURE_OPENAI:
        llm = get_openai_llm(azure=True)
        return get_openai_agent_executor(
            tools, llm, system_message, interrupt_before_action, CHECKPOINTER
        )
    elif agent == AgentType.CLAUDE2:
        llm = get_anthropic_llm()
        return get_xml_agent_executor(
            tools, llm, system_message, interrupt_before_action, CHECKPOINTER
        )
    elif agent == AgentType.BEDROCK_CLAUDE2:
        llm = get_anthropic_llm(bedrock=True)
        return get_xml_agent_executor(
            tools, llm, system_message, interrupt_before_action, CHECKPOINTER
        )
    elif agent == AgentType.GEMINI:
        llm = get_google_llm()
        return get_google_agent_executor(
            tools, llm, system_message, interrupt_before_action, CHECKPOINTER
        )
    else:
        raise ValueError("Unexpected agent type")


class ConfigurableAgent(RunnableBinding):
    tools: Sequence[Tool]
    agent: AgentType
    system_message: str = DEFAULT_SYSTEM_MESSAGE
    retrieval_description: str = RETRIEVAL_DESCRIPTION
    interrupt_before_action: bool = False
    assistant_id: Optional[str] = None
    thread_id: Optional[str] = None
    user_id: Optional[str] = None

    def __init__(
        self,
        *,
        tools: Sequence[Tool],
        agent: AgentType = AgentType.GPT_35_TURBO,
        system_message: str = DEFAULT_SYSTEM_MESSAGE,
        assistant_id: Optional[str] = None,
        thread_id: Optional[str] = None,
        retrieval_description: str = RETRIEVAL_DESCRIPTION,
        interrupt_before_action: bool = False,
        kwargs: Optional[Mapping[str, Any]] = None,
        config: Optional[Mapping[str, Any]] = None,
        **others: Any,
    ) -> None:
        others.pop("bound", None)
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
        _agent = get_agent_executor(
            _tools,
            agent,
            system_message,
            interrupt_before_action,
            assistant_id=assistant_id,
        )
        agent_executor = _agent.with_config({"recursion_limit": 50})
        super().__init__(
            tools=tools,
            agent=agent,
            system_message=system_message,
            retrieval_description=retrieval_description,
            bound=agent_executor,
            kwargs=kwargs or {},
            config=config or {},
        )


class LLMType(str, Enum):
    GPT_35_TURBO = "GPT 3.5 Turbo"
    # GPT_4 = "GPT 4 Turbo"
    # AZURE_OPENAI = "GPT 4 (Azure OpenAI)"
    # CLAUDE2 = "Claude 2"
    # BEDROCK_CLAUDE2 = "Claude 2 (Amazon Bedrock)"
    # GEMINI = "GEMINI"
    # MIXTRAL = "Mixtral"


def get_chatbot(
    llm_type: LLMType,
    system_message: str,
    assistant_id: Optional[str] = None,
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
    else:
        raise ValueError("Unexpected llm type")
    if assistant_id is not None:
        few_shot_example_string = few_shot_examples(assistant_id)
    else:
        few_shot_example_string = ""
    message = system_message + few_shot_example_string
    return get_chatbot_executor(llm, message, CHECKPOINTER)


class ConfigurableChatBot(RunnableBinding):
    llm: LLMType
    system_message: str = DEFAULT_SYSTEM_MESSAGE
    user_id: Optional[str] = None
    assistant_id: Optional[str] = None

    def __init__(
        self,
        *,
        llm: LLMType = LLMType.GPT_35_TURBO,
        system_message: str = DEFAULT_SYSTEM_MESSAGE,
        assistant_id: Optional[str] = None,
        kwargs: Optional[Mapping[str, Any]] = None,
        config: Optional[Mapping[str, Any]] = None,
        **others: Any,
    ) -> None:
        others.pop("bound", None)

        chatbot = get_chatbot(llm, system_message, assistant_id)
        super().__init__(
            llm=llm,
            system_message=system_message,
            bound=chatbot,
            kwargs=kwargs or {},
            config=config or {},
        )


chatbot = ConfigurableChatBot(
    llm=LLMType.GPT_35_TURBO, checkpoint=CHECKPOINTER
).configurable_fields(
    llm=ConfigurableField(id="llm_type", name="LLM Type"),
    system_message=ConfigurableField(id="system_message", name="Instructions"),
    assistant_id=ConfigurableField(
        id="assistant_id", name="Assistant ID", is_shared=True
    ),
)


class ConfigurableRetrieval(RunnableBinding):
    llm_type: LLMType
    system_message: str = DEFAULT_SYSTEM_MESSAGE
    assistant_id: Optional[str] = None
    thread_id: Optional[str] = None
    user_id: Optional[str] = None

    def __init__(
        self,
        *,
        llm_type: LLMType = LLMType.GPT_35_TURBO,
        system_message: str = DEFAULT_SYSTEM_MESSAGE,
        assistant_id: Optional[str] = None,
        thread_id: Optional[str] = None,
        kwargs: Optional[Mapping[str, Any]] = None,
        config: Optional[Mapping[str, Any]] = None,
        **others: Any,
    ) -> None:
        others.pop("bound", None)
        retriever = get_retriever(assistant_id, thread_id)
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
        else:
            raise ValueError("Unexpected llm type")
        chatbot = get_retrieval_executor(llm, retriever, system_message, CHECKPOINTER)
        super().__init__(
            llm_type=llm_type,
            system_message=system_message,
            bound=chatbot,
            kwargs=kwargs or {},
            config=config or {},
        )


chat_retrieval = ConfigurableRetrieval(
    llm_type=LLMType.GPT_35_TURBO, checkpoint=CHECKPOINTER
).configurable_fields(
    llm_type=ConfigurableField(id="llm_type", name="LLM Type"),
    system_message=ConfigurableField(id="system_message", name="Instructions"),
    assistant_id=ConfigurableField(
        id="assistant_id", name="Assistant ID", is_shared=True
    ),
    thread_id=ConfigurableField(id="thread_id", name="Thread ID", is_shared=True),
)


agent_w_tools = ConfigurableAgent(
    agent=AgentType.GPT_35_TURBO,
    tools=[],
    system_message=DEFAULT_SYSTEM_MESSAGE,
    retrieval_description=RETRIEVAL_DESCRIPTION,
    assistant_id=None,
    thread_id=None,
).configurable_fields(
    agent=ConfigurableField(id="agent_type", name="Agent Type"),
    system_message=ConfigurableField(id="system_message", name="Instructions"),
    interrupt_before_action=ConfigurableField(
        id="interrupt_before_action",
        name="Tool Confirmation",
        description="If Yes, you'll be prompted to continue before each tool is executed.\nIf No, tools will be executed automatically by the agent.",
    ),
    assistant_id=ConfigurableField(
        id="assistant_id", name="Assistant ID", is_shared=True
    ),
    thread_id=ConfigurableField(id="thread_id", name="Thread ID", is_shared=True),
    tools=ConfigurableField(id="tools", name="Tools"),
    retrieval_description=ConfigurableField(
        id="retrieval_description", name="Retrieval Description"
    ),
)


agent = chatbot.configurable_alternatives(
    ConfigurableField(id="type", name="Bot Type"),
    default_key="chatbot",
    prefix_keys=True,
    # chatbot=chatbot,
    # chat_retrieval=chat_retrieval,
).with_types(input_type=Sequence[AnyMessage], output_type=Sequence[AnyMessage])

if __name__ == "__main__":
    import asyncio

    from langchain.schema.messages import HumanMessage

    async def run():
        async for m in agent.astream_events(
            HumanMessage(content="whats your name"),
            config={"configurable": {"user_id": "2", "thread_id": "test1"}},
            version="v1",
        ):
            print(m)

    asyncio.run(run())
