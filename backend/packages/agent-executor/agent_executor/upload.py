from typing import Any, BinaryIO, List, Optional

from langchain.schema.runnable import RunnableConfig, RunnableSerializable
from langchain.schema.vectorstore import VectorStore
from langchain.text_splitter import TextSplitter


class IngestRunnable(RunnableSerializable[BinaryIO, List[str]]):
    text_splitter: TextSplitter
    vectorstore: VectorStore
    input_key: str
    assistant_id: Optional[str]

    class Config:
        arbitrary_types_allowed = True

    @property
    def namespace(self) -> str:
        if self.assistant_id is None:
            raise ValueError("assistant_id must be provided")
        return self.assistant_id

    def invoke(
        self, input: BinaryIO, config: Optional[RunnableConfig] = None
    ) -> List[str]:
        return self.batch([input], config)

    def batch(
        self,
        inputs: List[BinaryIO],
        config: RunnableConfig | List[RunnableConfig] | None = None,
        *,
        return_exceptions: bool = False,
        **kwargs: Any | None,
    ) -> List:
        docs = self.text_splitter.create_documents(
            # TODO change this line to accept binary formats
            [part.read().decode() for part in inputs],
            [{"namespace": self.namespace}],
        )
        return self.vectorstore.add_documents(docs)
