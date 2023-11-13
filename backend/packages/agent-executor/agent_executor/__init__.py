from __future__ import annotations

import asyncio
import json
import logging
import time
from typing import (
    Any,
    AsyncIterator,
    Callable,
    Dict,
    List,
    Optional,
    Sequence,
    Tuple,
    Union,
)

from langchain.agents.agent import ExceptionTool
from langchain.agents.tools import InvalidTool
from langchain.callbacks.manager import (
    AsyncCallbackManager,
    AsyncCallbackManagerForChainRun,
)
from langchain.load.dump import dumpd
from langchain.load.serializable import Serializable
from langchain.schema import (
    AgentAction,
    AgentFinish,
    OutputParserException,
)
from langchain.schema.agent import AgentActionMessageLog
from langchain.schema.messages import (
    AIMessage,
    BaseMessage,
    FunctionMessage,
)
from langchain.schema.runnable import Runnable, RunnableSerializable
from langchain.schema.runnable.config import RunnableConfig
from langchain.schema.runnable.utils import AddableDict, Input, Output
from langchain.tools.base import BaseTool
from langchain.utilities.asyncio import asyncio_timeout
from langchain.utils.input import get_color_mapping

logger = logging.getLogger(__name__)


def _create_function_message(
    agent_action: AgentAction, observation: str
) -> FunctionMessage:
    """Convert agent action and observation into a function message.
    Args:
        agent_action: the tool invocation request from the agent
        observation: the result of the tool invocation
    Returns:
        FunctionMessage that corresponds to the original tool invocation
    """
    if not isinstance(observation, str):
        try:
            content = json.dumps(observation, ensure_ascii=False)
        except Exception:
            content = str(observation)
    else:
        content = observation
    return FunctionMessage(
        name=agent_action.tool,
        content=content,
    )


def _convert_agent_observation_to_messages(
    agent_action: AgentAction, observation: Any
) -> Sequence[BaseMessage]:
    """Convert an agent action to a message.

    This code is used to reconstruct the original AI message from the agent action.

    Args:
        agent_action: Agent action to convert.

    Returns:
        AIMessage that corresponds to the original tool invocation.
    """
    return [_create_function_message(agent_action, observation)]


class AgentStep(Serializable):
    """The result of running an AgentAction."""

    action: AgentAction
    """The AgentAction that was executed."""
    observation: Any
    """The result of the AgentAction."""

    @property
    def messages(self) -> Sequence[BaseMessage]:
        """Return the messages that correspond to this observation."""
        return _convert_agent_observation_to_messages(self.action, self.observation)


NextStepOutput = List[Union[AgentFinish, AgentAction, AgentStep]]


class AgentExecutor(RunnableSerializable):
    agent: Runnable
    """The agent to run for creating a plan and determining actions
    to take at each step of the execution loop."""
    tools: Sequence[BaseTool]
    """The valid tools the agent can call."""
    max_iterations: Optional[int] = 15
    """The maximum number of steps to take before ending the execution
    loop.

    Setting to 'None' could lead to an infinite loop."""
    max_execution_time: Optional[float] = None
    """The maximum amount of wall clock time to spend in the execution
    loop.
    """
    early_stopping_method: str = "force"
    """The method to use for early stopping if the agent never
    returns `AgentFinish`. Either 'force' or 'generate'.

    `"force"` returns a string saying that it stopped because it met a
        time or iteration limit.

    `"generate"` calls the agent's LLM Chain one final time to generate
        a final answer based on the previous steps.
    """
    handle_parsing_errors: Union[
        bool, str, Callable[[OutputParserException], str]
    ] = False
    """How to handle errors raised by the agent's output parser.
    Defaults to `False`, which raises the error.
    If `true`, the error will be sent back to the LLM as an observation.
    If a string, the string itself will be sent to the LLM as an observation.
    If a callable function, the function will be called with the exception
     as an argument, and the result of that function will be passed to the agent
      as an observation.
    """

    class Config:
        """Configuration for this pydantic object."""

        arbitrary_types_allowed = True

    def invoke(self, input: Input, config: Optional[RunnableConfig] = None) -> Output:
        raise ValueError

    def _should_continue(self, iterations: int, time_elapsed: float) -> bool:
        if self.max_iterations is not None and iterations >= self.max_iterations:
            return False
        if (
            self.max_execution_time is not None
            and time_elapsed >= self.max_execution_time
        ):
            return False

        return True

    @property
    def name_to_tool_map(self) -> Dict[str, BaseTool]:
        return {tool.name: tool for tool in self.tools}

    @property
    def color_mapping(self) -> Dict[str, str]:
        return get_color_mapping(
            [tool.name for tool in self.tools],
            excluded_colors=["green", "red"],
        )

    def _get_tool_return(
        self, next_step_output: Tuple[AgentAction, str]
    ) -> Optional[AgentFinish]:
        """Check if the tool is a returning tool."""
        agent_action, observation = next_step_output
        name_to_tool_map = {tool.name: tool for tool in self.tools}
        return_value_key = "output"
        # Invalid tools won't be in the map, so we return False.
        if agent_action.tool in name_to_tool_map:
            if name_to_tool_map[agent_action.tool].return_direct:
                return AgentFinish(
                    {return_value_key: observation},
                    "",
                )
        return None

    def return_stopped_response(
        self,
        early_stopping_method: str,
        intermediate_steps: List[Tuple[AgentAction, str]],
        **kwargs: Any,
    ) -> AgentFinish:
        """Return response when agent has been stopped due to max iterations."""
        if early_stopping_method == "force":
            # `force` just returns a constant string
            return AgentFinish(
                {"output": "Agent stopped due to iteration limit or time limit."}, ""
            )
        else:
            raise ValueError(
                "early_stopping_method should be one of `force` or `generate`, "
                f"got {early_stopping_method}"
            )

    async def _aprocess_next_step_output(
        self,
        next_step_output: Union[AgentFinish, List[Tuple[AgentAction, str]]],
        intermediate_steps,
        run_manager: AsyncCallbackManagerForChainRun,
        acc_output: AddableDict,
    ) -> Optional[AddableDict]:
        """
        Process the output of the next async step,
        handling AgentFinish and tool return cases.
        """
        logger.debug("Processing output of async Agent loop step")
        if isinstance(next_step_output, AgentFinish):
            logger.debug(
                "Hit AgentFinish: _areturn -> on_chain_end -> run final output logic"
            )
            return await self._areturn(
                next_step_output, run_manager=run_manager, acc_output=acc_output
            )

        intermediate_steps.extend(next_step_output)
        logger.debug("Updated intermediate_steps with step output")

        # Check for tool return
        if len(next_step_output) == 1:
            next_step_action = next_step_output[0]
            tool_return = self._get_tool_return(next_step_action)
            if tool_return is not None:
                return await self._areturn(
                    tool_return, run_manager=run_manager, acc_output=acc_output
                )

    async def _aiter_next_step(
        self,
        name_to_tool_map: Dict[str, BaseTool],
        color_mapping: Dict[str, str],
        inputs: Dict[str, str],
        intermediate_steps: List[Tuple[AgentAction, str]],
        run_manager: Optional[AsyncCallbackManagerForChainRun] = None,
    ) -> AsyncIterator[Union[AgentFinish, AgentAction, AgentStep]]:
        """Take a single step in the thought-action-observation loop.

        Override this to take control of how the agent makes and acts on choices.
        """
        try:
            _inputs = {**{"intermediate_steps": intermediate_steps}, **inputs}
            # Call the LLM to see what to do.
            output = await self.agent.ainvoke(
                _inputs,
                config={"callbacks": run_manager.get_child() if run_manager else None},
            )
        except OutputParserException as e:
            if isinstance(self.handle_parsing_errors, bool):
                raise_error = not self.handle_parsing_errors
            else:
                raise_error = False
            if raise_error:
                raise ValueError(
                    "An output parsing error occurred. "
                    "In order to pass this error back to the agent and have it try "
                    "again, pass `handle_parsing_errors=True` to the AgentExecutor. "
                    f"This is the error: {str(e)}"
                )
            text = str(e)
            if isinstance(self.handle_parsing_errors, bool):
                if e.send_to_llm:
                    observation = str(e.observation)
                    text = str(e.llm_output)
                else:
                    observation = "Invalid or incomplete response"
            elif isinstance(self.handle_parsing_errors, str):
                observation = self.handle_parsing_errors
            elif callable(self.handle_parsing_errors):
                observation = self.handle_parsing_errors(e)
            else:
                raise ValueError("Got unexpected type of `handle_parsing_errors`")
            output = AgentAction("_Exception", observation, text)
            observation = await ExceptionTool().arun(
                output.tool_input,
                color=None,
                callbacks=run_manager.get_child() if run_manager else None,
            )
            yield AgentStep(action=output, observation=observation)
            return

        # If the tool chosen is the finishing tool, then we end and return.
        if isinstance(output, AgentFinish):
            yield output
            return

        yield output

        if run_manager:
            await run_manager.on_agent_action(output, color="green")
        # Otherwise we lookup the tool
        if output.tool in name_to_tool_map:
            tool = name_to_tool_map[output.tool]
            color = color_mapping[output.tool]
            # We then call the tool on the tool input to get an observation
            observation = await tool.arun(
                output.tool_input,
                color=color,
                callbacks=run_manager.get_child() if run_manager else None,
            )
        else:
            observation = await InvalidTool().arun(
                {
                    "requested_tool_name": output.tool,
                    "available_tool_names": list(name_to_tool_map.keys()),
                },
                color=None,
                callbacks=run_manager.get_child() if run_manager else None,
            )
        yield AgentStep(action=output, observation=observation)

    async def _astop(
        self,
        inputs,
        intermediate_steps,
        run_manager: AsyncCallbackManagerForChainRun,
        acc_output: AddableDict,
    ) -> AddableDict:
        """
        Stop the async iterator and raise a StopAsyncIteration exception with
        the stopped response.
        """
        logger.warning("Stopping agent prematurely due to triggering stop condition")
        output = self.return_stopped_response(
            self.early_stopping_method,
            intermediate_steps,
            **inputs,
        )
        return await self._areturn(
            output, run_manager=run_manager, acc_output=acc_output
        )

    def _consume_next_step(
        self, values: NextStepOutput
    ) -> Union[AgentFinish, List[Tuple[AgentAction, str]]]:
        if isinstance(values[-1], AgentFinish):
            assert len(values) == 1
            return values[-1]
        else:
            return [
                (a.action, a.observation) for a in values if isinstance(a, AgentStep)
            ]

    async def _areturn(
        self,
        output: AgentFinish,
        run_manager: AsyncCallbackManagerForChainRun,
        acc_output: AddableDict,
    ) -> AddableDict:
        """
        Return the final output of the async iterator.
        """
        if run_manager:
            await run_manager.on_agent_finish(output, color="green")
        final_output = AddableDict(output.return_values)
        final_output["messages"] = [AIMessage(content=output.log)]
        await run_manager.on_chain_end(acc_output + final_output)
        return final_output

    async def astream(
        self,
        input: Union[Dict[str, Any], Any],
        config: Optional[RunnableConfig] = None,
        **kwargs: Any,
    ) -> AsyncIterator[AddableDict]:
        """Enables streaming over steps taken to reach final output."""
        config = config or {}
        run_name = config.get("run_name")
        iterations = 0
        start_time = time.time()
        time_elapsed = 0
        intermediate_steps = []
        logger.debug("Initialising AgentExecutorIterator (async)")
        callback_manager = AsyncCallbackManager.configure(
            inheritable_callbacks=config.get("callbacks"),
            inheritable_metadata=config.get("metadata"),
            inheritable_tags=config.get("tags"),
        )
        run_manager = await callback_manager.on_chain_start(
            dumpd(self),
            input,
            name=run_name,
        )
        try:
            async with asyncio_timeout(self.max_execution_time):
                acc_output = AddableDict()
                while self._should_continue(iterations, time_elapsed):
                    # take the next step: this plans next action, executes it,
                    # yielding action and observation as they are generated
                    next_step_seq: NextStepOutput = []
                    async for chunk in self._aiter_next_step(
                        self.name_to_tool_map,
                        self.color_mapping,
                        input,
                        intermediate_steps,
                        run_manager,
                    ):
                        next_step_seq.append(chunk)
                        # do not yield AgentFinish, which will be handled below
                        if isinstance(chunk, AgentAction):
                            if isinstance(chunk, AgentActionMessageLog):
                                next_output = AddableDict(
                                    actions=[chunk], messages=chunk.message_log
                                )
                                acc_output += next_output
                                yield next_output
                            else:
                                msg = AIMessage(
                                    content=chunk.log,
                                    additional_kwargs={
                                        "function_call": {
                                            "name": chunk.tool,
                                            "arguments": json.dumps(
                                                {"input": chunk.tool_input}
                                            ),
                                        }
                                    },
                                )
                                next_output = AddableDict(
                                    actions=[chunk],
                                    messages=[msg],
                                )
                                acc_output += next_output
                                yield next_output

                        elif isinstance(chunk, AgentStep):
                            next_output = AddableDict(
                                steps=[chunk], messages=chunk.messages
                            )
                            acc_output += next_output
                            yield next_output

                    # convert iterator output to format handled by _process_next_step
                    next_step = self._consume_next_step(next_step_seq)
                    # update iterations and time elapsed
                    iterations += 1
                    time_elapsed = time.time() - start_time
                    # decide if this is the final output
                    if output := await self._aprocess_next_step_output(
                        next_step, intermediate_steps, run_manager, acc_output
                    ):
                        yield output
                        return
        except (TimeoutError, asyncio.TimeoutError):
            yield await self._astop(input, intermediate_steps, run_manager, acc_output)
            return
        except BaseException as e:
            await run_manager.on_chain_error(e)
            raise

        # if we got here means we exhausted iterations or time
        yield await self._astop(input, intermediate_steps, run_manager, acc_output)
