"""API to deal with file uploads via a runnable.

For now this code assumes that the content is a base64 encoded string.

The details here might change in the future.

For the time being, upload and ingestion are coupled
"""
from __future__ import annotations

import base64
from typing import Optional, Sequence
import base64
from typing import Optional, Sequence

from langchain.document_loaders.blob_loaders.schema import Blob
from langchain.schema.runnable import RunnableConfig, RunnableSerializable
from langchain.schema.runnable.utils import ConfigurableFieldSpec
from langchain.schema.vectorstore import VectorStore
from langchain.text_splitter import TextSplitter
from typing_extensions import NotRequired, TypedDict

from agent_executor.ingest import ingest_blob
from agent_executor.parsing import MIMETYPE_BASED_PARSER

from langchain.document_loaders.blob_loaders.schema import Blob
from langchain.schema.runnable import RunnableConfig, RunnableSerializable
from langchain.schema.runnable.utils import ConfigurableFieldSpec
from langchain.schema.vectorstore import VectorStore
from langchain.text_splitter import TextSplitter
from typing_extensions import NotRequired, TypedDict

from agent_executor.ingest import ingest_blob
from agent_executor.parsing import MIMETYPE_BASED_PARSER


def _guess_mimetype(file_bytes: bytes) -> str:
    """Guess the mime-type of a file."""
    try:
        import magic
    except ImportError:
        raise ImportError(
            "magic package not found, please install it with `pip install python-magic`"
        )

    mime = magic.Magic(mime=True)
    mime_type = mime.from_buffer(file_bytes)
    return mime_type


def _convert_ingestion_input_to_blob(ingestion_input: IngestionInput) -> Blob:
    """Convert ingestion input to blob."""
    base64_file = ingestion_input["file_contents"]
    file_data = base64.decodebytes(base64_file.encode("utf-8"))
    mimetype = _guess_mimetype(file_data)
    filename = ingestion_input["filename"] if "filename" in ingestion_input else None
    return Blob.from_data(
        data=file_data,
        path=filename,
        mime_type=mimetype,
    )




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
