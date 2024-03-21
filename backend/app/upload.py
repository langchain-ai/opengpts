"""API to deal with file uploads via a runnable.

For now this code assumes that the content is a base64 encoded string.

The details here might change in the future.

For the time being, upload and ingestion are coupled
"""
from __future__ import annotations

import os
import httpx
import logging
from typing import Any, BinaryIO, List, Optional, Union
from urllib.parse import urlparse

from langchain_text_splitters import RecursiveCharacterTextSplitter, TextSplitter
from langchain_community.document_loaders.blob_loaders.schema import Blob
from langchain_community.vectorstores.pgvector import PGVector
from langchain_core.runnables import (
    ConfigurableField,
    RunnableConfig,
    RunnableSerializable,
)
from langchain_core.vectorstores import VectorStore
from langchain_openai import OpenAIEmbeddings

from app.ingest import ingest_blob
from app.parsing import MIMETYPE_BASED_PARSER

logger = logging.getLogger(__name__)


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


def _get_http_client(use_async: bool = False) -> Union[httpx.Client, httpx.AsyncClient]:
    """
    Create and return a httpx.Client or httpx.AsyncClient instance, configured with a proxy if available and valid.

    The method checks for a PROXY_URL environment variable. If a valid proxy URL is found,
    the client is configured to use this proxy. Otherwise, a default client is returned.

    Args:
        use_async (bool): Flag indicating whether to return an asynchronous HTTP client.

    Returns:
        An instance of httpx.Client or httpx.AsyncClient configured with or without a proxy based on the environment configuration.
    """
    proxy_url = os.getenv("PROXY_URL")
    client_kwargs = {}
    if proxy_url:
        parsed_url = urlparse(proxy_url)
        if parsed_url.scheme and parsed_url.netloc:
            client_kwargs["proxies"] = proxy_url
        else:
            logger.warning("Invalid proxy URL provided. Proceeding without proxy.")

    if use_async:
        return httpx.AsyncClient(**client_kwargs)
    else:
        return httpx.Client(**client_kwargs)


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
        return self.batch([input], config)

    def batch(
            self,
            inputs: List[BinaryIO],
            config: RunnableConfig | List[RunnableConfig] | None = None,
            *,
            return_exceptions: bool = False,
            **kwargs: Any | None,
    ) -> List:
        """Ingest a batch of files into the vectorstore."""
        ids = []
        for data in inputs:
            blob = _convert_ingestion_input_to_blob(data)
            ids.extend(
                ingest_blob(
                    blob,
                    MIMETYPE_BASED_PARSER,
                    self.text_splitter,
                    self.vectorstore,
                    self.namespace,
                )
            )
        return ids


PG_CONNECTION_STRING = PGVector.connection_string_from_db_params(
    driver="psycopg2",
    host=os.environ["POSTGRES_HOST"],
    port=int(os.environ["POSTGRES_PORT"]),
    database=os.environ["POSTGRES_DB"],
    user=os.environ["POSTGRES_USER"],
    password=os.environ["POSTGRES_PASSWORD"],
)
vstore = PGVector(
    connection_string=PG_CONNECTION_STRING,
    embedding_function=OpenAIEmbeddings(http_client=_get_http_client()),
    use_jsonb=True,
)

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
