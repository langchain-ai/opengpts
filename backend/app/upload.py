"""API to deal with file uploads via a runnable.

For now this code assumes that the content is a base64 encoded string.

The details here might change in the future.

For the time being, upload and ingestion are coupled
"""

from __future__ import annotations

import os
from typing import BinaryIO, List, Optional

from langchain_core.document_loaders.blob_loaders import Blob
from langchain_community.vectorstores.pgvector import PGVector
from langchain_core.runnables import (
    ConfigurableField,
    RunnableConfig,
    RunnableSerializable,
)
from langchain_core.vectorstores import VectorStore
from langchain_openai import AzureOpenAIEmbeddings, OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter, TextSplitter

from app.ingest import ingest_blob
from app.parsing import MIMETYPE_BASED_PARSER


def _guess_mimetype(file_bytes: bytes) -> str:
    """Guess the mime-type of a file."""
    try:
        import magic
    except ImportError as e:
        raise ImportError(
            "magic package not found, please install it with `pip install python-magic`"
        ) from e

    mime = magic.Magic(mime=True)
    mime_type = mime.from_buffer(file_bytes)
    return mime_type


def _convert_ingestion_input_to_blob(data: BinaryIO) -> Blob:
    """Convert ingestion input to blob."""
    file_data = data.read()
    mimetype = _guess_mimetype(file_data)
    file_name = data.name
    return Blob.from_data(
        data=file_data,
        path=file_name,
        mime_type=mimetype,
    )


def _determine_azure_or_openai_embeddings() -> PGVector:
    if os.environ.get("OPENAI_API_KEY"):
        return PGVector(
            connection_string=PG_CONNECTION_STRING,
            embedding_function=OpenAIEmbeddings(),
            use_jsonb=True,
        )
    if os.environ.get("AZURE_OPENAI_API_KEY"):
        return PGVector(
            connection_string=PG_CONNECTION_STRING,
            embedding_function=AzureOpenAIEmbeddings(
                azure_endpoint=os.environ.get("AZURE_OPENAI_API_BASE"),
                azure_deployment=os.environ.get(
                    "AZURE_OPENAI_EMBEDDINGS_DEPLOYMENT_NAME"
                ),
                openai_api_version=os.environ.get("AZURE_OPENAI_API_VERSION"),
            ),
            use_jsonb=True,
        )
    raise ValueError(
        "Either OPENAI_API_KEY or AZURE_OPENAI_API_KEY needs to be set for embeddings to work."
    )


class IngestRunnable(RunnableSerializable[BinaryIO, List[str]]):
    """Runnable for ingesting files into a vectorstore."""

    text_splitter: TextSplitter
    """Text splitter to use for splitting the text into chunks."""
    vectorstore: VectorStore
    """Vectorstore to ingest into."""
    assistant_id: Optional[str]
    thread_id: Optional[str]
    """Ingested documents will be associated with assistant_id or thread_id.
    
    ID is used as the namespace, and is filtered on at query time.
    """

    class Config:
        arbitrary_types_allowed = True

    @property
    def namespace(self) -> str:
        if (self.assistant_id is None and self.thread_id is None) or (
            self.assistant_id is not None and self.thread_id is not None
        ):
            raise ValueError(
                "Exactly one of assistant_id or thread_id must be provided"
            )
        return self.assistant_id if self.assistant_id is not None else self.thread_id

    def invoke(
        self, input: BinaryIO, config: Optional[RunnableConfig] = None
    ) -> List[str]:
        blob = _convert_ingestion_input_to_blob(input)
        out = ingest_blob(
            blob,
            MIMETYPE_BASED_PARSER,
            self.text_splitter,
            self.vectorstore,
            self.namespace,
        )
        return out


PG_CONNECTION_STRING = PGVector.connection_string_from_db_params(
    driver="psycopg2",
    host=os.environ["POSTGRES_HOST"],
    port=int(os.environ["POSTGRES_PORT"]),
    database=os.environ["POSTGRES_DB"],
    user=os.environ["POSTGRES_USER"],
    password=os.environ["POSTGRES_PASSWORD"],
)
vstore = _determine_azure_or_openai_embeddings()


ingest_runnable = IngestRunnable(
    text_splitter=RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200),
    vectorstore=vstore,
).configurable_fields(
    assistant_id=ConfigurableField(
        id="assistant_id",
        annotation=str,
        name="Assistant ID",
    ),
    thread_id=ConfigurableField(
        id="thread_id",
        annotation=str,
        name="Thread ID",
    ),
)
