"""API to deal with file uploads via a runnable.

For now this code assumes that the content is a base64 encoded string.

The details here might change in the future.

For the time being, upload and ingestion are coupled
"""
from __future__ import annotations

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


# PUBLIC API


class IngestionInput(TypedDict):
    """Input to the ingestion runnable."""

    # For now the file contents are base 64 encoded files
    file_contents: str
    filename: NotRequired[str]


class IngestionOutput(TypedDict):
    """Output of the ingestion runnable."""

    success: bool


class IngestRunnable(RunnableSerializable[IngestionInput, IngestionOutput]):
    text_splitter: TextSplitter
    vectorstore: VectorStore
    namespace: str = ""

    class Config:
        arbitrary_types_allowed = True

    def invoke(
        self, input: IngestionInput, config: Optional[RunnableConfig] = None
    ) -> IngestionOutput:
        """Ingest a document into the vectorstore."""
        if not self.namespace:
            raise ValueError("namespace must be provided")

        blob = _convert_ingestion_input_to_blob(input)
        ingest_blob(
            blob,
            MIMETYPE_BASED_PARSER,
            self.text_splitter,
            self.vectorstore,
            namespace=self.namespace,
        )
        return {"success": True}

    @property
    def config_specs(self) -> Sequence[ConfigurableFieldSpec]:
        """Configurable fields for this runnable."""
        return list(super().config_specs) + [
            ConfigurableFieldSpec(
                id="namespace",
                annotation=str,
                name="",
                description="",
                default="",
            )
        ]
