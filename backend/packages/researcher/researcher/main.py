from typing import Any, Mapping, Optional, Sequence
from enum import Enum
from langchain.pydantic_v1 import BaseModel, Field
from langchain.schema.messages import AnyMessage
from langchain.schema.runnable import (
    ConfigurableField,
    ConfigurableFieldMultiOption,
    RunnableBinding,
)

from agent_executor.checkpoint import RedisCheckpoint
from researcher.writer import chain as writer_chain
from researcher.search import chain as search_chain
from researcher.permchain_agent import get_agent_executor

class LLMType(Enum):
    GPT_35_TURBO = "GPT 3.5 Turbo"


class ConfigurableResearcher(RunnableBinding):
    llm_type: LLMType

    def __init__(
        self,
        *,
        llm_type: LLMType,
        kwargs: Optional[Mapping[str, Any]] = None,
        config: Optional[Mapping[str, Any]] = None,
        **others: Any,
    ) -> None:
        others.pop("bound", None)
        _tools = []

        if llm_type == LLMType.GPT_35_TURBO:
            agent_executor = get_agent_executor(
                search=search_chain, writer=writer_chain,checkpoint=RedisCheckpoint()
            ).with_config({"recursion_limit": 10})
        else:
            raise ValueError("Unexpected agent type")

        super().__init__(
            llm_type=llm_type,
            bound=agent_executor,
            kwargs=kwargs or {},
            config=config or {},
        )


class AgentInput(BaseModel):
    question: str


class AgentOutput(BaseModel):
    draft: str


agent = (
    ConfigurableResearcher(
        llm_type=LLMType.GPT_35_TURBO
    )
    .configurable_fields(
        llm_type=ConfigurableField(id="llm_type", name="LLM type"),
    )
    .with_types(input_type=AgentInput, output_type=AgentOutput)
)

if __name__ == "__main__":
    import asyncio

    from langchain.schema.messages import HumanMessage

    async def run():
        async for m in agent.astream_log(
            {"question": HumanMessage(content="what other papers did the authors of the transformers paper write?")},
                config={"configurable": {"user_id": "1", "thread_id": "test1"}}
        ):
            print(m)

    asyncio.run(run())