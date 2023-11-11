"""Temporary code for RunnableBinding.

This is temporary code for Runnable Binding while it isn't available on released
LangChain.
"""
from __future__ import annotations

from typing import (
    Any,
    AsyncIterator,
    Callable,
    Iterator,
    List,
    Mapping,
    Optional,
    Sequence,
    Type,
    TypeVar,
    Union,
    cast,
)

from langchain.pydantic_v1 import BaseModel, Field
from langchain.schema.runnable import Runnable, RunnableSerializable
from langchain.schema.runnable.config import (
    RunnableConfig,
    merge_configs,
)
from langchain.schema.runnable.utils import (
    ConfigurableFieldSpec,
    Input,
    Output,
)

Other = TypeVar("Other")


class RunnableBindingBase(RunnableSerializable[Input, Output]):
    """A runnable that delegates calls to another runnable with a set of kwargs."""

    bound: Runnable[Input, Output]

    kwargs: Mapping[str, Any] = Field(default_factory=dict)

    config: RunnableConfig = Field(default_factory=dict)

    config_factories: List[Callable[[RunnableConfig], RunnableConfig]] = Field(
        default_factory=list
    )

    # Union[Type[Input], BaseModel] + things like List[str]
    custom_input_type: Optional[Any] = None
    # Union[Type[Output], BaseModel] + things like List[str]
    custom_output_type: Optional[Any] = None

    class Config:
        arbitrary_types_allowed = True

    def __init__(
        self,
        *,
        bound: Runnable[Input, Output],
        kwargs: Optional[Mapping[str, Any]] = None,
        config: Optional[RunnableConfig] = None,
        config_factories: Optional[
            List[Callable[[RunnableConfig], RunnableConfig]]
        ] = None,
        custom_input_type: Optional[Union[Type[Input], BaseModel]] = None,
        custom_output_type: Optional[Union[Type[Output], BaseModel]] = None,
        **other_kwargs: Any,
    ) -> None:
        config = config or {}
        # config_specs contains the list of valid `configurable` keys
        if configurable := config.get("configurable", None):
            allowed_keys = set(s.id for s in bound.config_specs)
            for key in configurable:
                if key not in allowed_keys:
                    raise ValueError(
                        f"Configurable key '{key}' not found in runnable with"
                        f" config keys: {allowed_keys}"
                    )
        super().__init__(
            bound=bound,
            kwargs=kwargs or {},
            config=config or {},
            config_factories=config_factories or [],
            custom_input_type=custom_input_type,
            custom_output_type=custom_output_type,
            **other_kwargs,
        )

    @property
    def InputType(self) -> Type[Input]:
        return (
            cast(Type[Input], self.custom_input_type)
            if self.custom_input_type is not None
            else self.bound.InputType
        )

    @property
    def OutputType(self) -> Type[Output]:
        return (
            cast(Type[Output], self.custom_output_type)
            if self.custom_output_type is not None
            else self.bound.OutputType
        )

    def get_input_schema(
        self, config: Optional[RunnableConfig] = None
    ) -> Type[BaseModel]:
        if self.custom_input_type is not None:
            return super().get_input_schema(config)
        return self.bound.get_input_schema(merge_configs(self.config, config))

    def get_output_schema(
        self, config: Optional[RunnableConfig] = None
    ) -> Type[BaseModel]:
        if self.custom_output_type is not None:
            return super().get_output_schema(config)
        return self.bound.get_output_schema(merge_configs(self.config, config))

    @property
    def config_specs(self) -> Sequence[ConfigurableFieldSpec]:
        return self.bound.config_specs

    @classmethod
    def is_lc_serializable(cls) -> bool:
        return True

    @classmethod
    def get_lc_namespace(cls) -> List[str]:
        return cls.__module__.split(".")[:-1]

    def _merge_configs(self, *configs: Optional[RunnableConfig]) -> RunnableConfig:
        config = merge_configs(self.config, *configs)
        return merge_configs(config, *(f(config) for f in self.config_factories))

    def invoke(
        self,
        input: Input,
        config: Optional[RunnableConfig] = None,
        **kwargs: Optional[Any],
    ) -> Output:
        return self.bound.invoke(
            input,
            self._merge_configs(config),
            **{**self.kwargs, **kwargs},
        )

    async def ainvoke(
        self,
        input: Input,
        config: Optional[RunnableConfig] = None,
        **kwargs: Optional[Any],
    ) -> Output:
        return await self.bound.ainvoke(
            input,
            self._merge_configs(config),
            **{**self.kwargs, **kwargs},
        )

    def batch(
        self,
        inputs: List[Input],
        config: Optional[Union[RunnableConfig, List[RunnableConfig]]] = None,
        *,
        return_exceptions: bool = False,
        **kwargs: Optional[Any],
    ) -> List[Output]:
        if isinstance(config, list):
            configs = cast(
                List[RunnableConfig],
                [self._merge_configs(conf) for conf in config],
            )
        else:
            configs = [self._merge_configs(config) for _ in range(len(inputs))]
        return self.bound.batch(
            inputs,
            configs,
            return_exceptions=return_exceptions,
            **{**self.kwargs, **kwargs},
        )

    async def abatch(
        self,
        inputs: List[Input],
        config: Optional[Union[RunnableConfig, List[RunnableConfig]]] = None,
        *,
        return_exceptions: bool = False,
        **kwargs: Optional[Any],
    ) -> List[Output]:
        if isinstance(config, list):
            configs = cast(
                List[RunnableConfig],
                [self._merge_configs(conf) for conf in config],
            )
        else:
            configs = [self._merge_configs(config) for _ in range(len(inputs))]
        return await self.bound.abatch(
            inputs,
            configs,
            return_exceptions=return_exceptions,
            **{**self.kwargs, **kwargs},
        )

    def stream(
        self,
        input: Input,
        config: Optional[RunnableConfig] = None,
        **kwargs: Optional[Any],
    ) -> Iterator[Output]:
        yield from self.bound.stream(
            input,
            self._merge_configs(config),
            **{**self.kwargs, **kwargs},
        )

    async def astream(
        self,
        input: Input,
        config: Optional[RunnableConfig] = None,
        **kwargs: Optional[Any],
    ) -> AsyncIterator[Output]:
        async for item in self.bound.astream(
            input,
            self._merge_configs(config),
            **{**self.kwargs, **kwargs},
        ):
            yield item

    def transform(
        self,
        input: Iterator[Input],
        config: Optional[RunnableConfig] = None,
        **kwargs: Any,
    ) -> Iterator[Output]:
        yield from self.bound.transform(
            input,
            self._merge_configs(config),
            **{**self.kwargs, **kwargs},
        )

    async def atransform(
        self,
        input: AsyncIterator[Input],
        config: Optional[RunnableConfig] = None,
        **kwargs: Any,
    ) -> AsyncIterator[Output]:
        async for item in self.bound.atransform(
            input,
            self._merge_configs(config),
            **{**self.kwargs, **kwargs},
        ):
            yield item


RunnableBindingBase.update_forward_refs(RunnableConfig=RunnableConfig)
