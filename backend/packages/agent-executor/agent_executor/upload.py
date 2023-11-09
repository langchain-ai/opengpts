from typing import Optional, Sequence

from langchain.schema.runnable import RunnableConfig, RunnableSerializable
from langchain.schema.runnable.utils import ConfigurableFieldSpec, Input, Output
from langchain.schema.vectorstore import VectorStore
from langchain.text_splitter import TextSplitter


class IngestRunnable(RunnableSerializable):
    text_splitter: TextSplitter
    vectorstore: VectorStore
    input_key: str
    namespace: str = ""

    class Config:
        arbitrary_types_allowed = True

    def invoke(self, input: Input, config: Optional[RunnableConfig] = None) -> Output:
        if not self.namespace:
            raise ValueError("namespace must be provided")
        docs = self.text_splitter.create_documents(
            [input[self.input_key]], [{"namespace": self.namespace}]
        )
        self.vectorstore.add_documents(docs)
        return {}

    @property
    def config_specs(self) -> Sequence[ConfigurableFieldSpec]:
        return super().config_specs + [
            ConfigurableFieldSpec(
                id="namespace",
                annotation=str,
                name="",
                description="",
                default="",
            )
        ]
