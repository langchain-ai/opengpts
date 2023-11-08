from typing import Optional

from langchain.schema.runnable import RunnableSerializable, RunnableConfig
from langchain.schema.runnable.utils import Input, Output
from langchain.text_splitter import RecursiveCharacterTextSplitter, TextSplitter
from langchain.schema.vectorstore import VectorStore


class IngestRunnable(RunnableSerializable):
    text_splitter: TextSplitter
    vectorstore: VectorStore
    input_key: str

    class Config:
        arbitrary_types_allowed = True

    def invoke(self, input: Input, config: Optional[RunnableConfig] = None) -> Output:
        docs = self.text_splitter.create_documents([input[self.input_key]],
                                                   [{"namespace": config["configurable"]["assistant_id"]}])
        self.vectorstore.add_documents(docs)