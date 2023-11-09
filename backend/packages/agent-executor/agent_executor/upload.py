import base64
from typing import List, NotRequired, Optional, Sequence

from langchain.document_loaders.base import BaseBlobParser
from langchain.document_loaders.blob_loaders.schema import Blob
from langchain.document_loaders.parsers import PyMuPDFParser
from langchain.document_loaders.parsers.generic import MimeTypeBasedParser
from langchain.document_loaders.parsers.html import BS4HTMLParser
from langchain.document_loaders.parsers.msword import MsWordParser
from langchain.document_loaders.parsers.txt import TextParser
from langchain.schema.runnable import RunnableConfig, RunnableSerializable
from langchain.schema.runnable.utils import ConfigurableFieldSpec
from langchain.schema.vectorstore import VectorStore
from langchain.text_splitter import TextSplitter


def _guess_mimetype(file_bytes: bytes) -> str:
    """Guess the mime-type of a file."""
    try:
        import magic
    except ImportError:
        raise ImportError(
            "magic package not found, please install it with `pip install python-magic`"
        )

    mime = magic.Magic()
    mime_type = mime.from_buffer(file_bytes)
    return mime_type


def _get_default_parser() -> BaseBlobParser:
    """Get default mime-type based parser."""
    return MimeTypeBasedParser(
        handlers={
            "application/pdf": PyMuPDFParser(),
            "text/plain": TextParser(),
            "text/html": BS4HTMLParser(),
            "application/msword": MsWordParser(),
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document": (
                MsWordParser()
            ),
        },
        fallback_parser=None,
    )


# PUBLIC API
from typing_extensions import TypedDict


class IngestionInput(TypedDict):
    """Input to the ingestion runnable."""

    base64_file: str
    filename: NotRequired[str]


class IngestionOutput(TypedDict):
    """Output of the ingestion runnable."""

    success: bool


def _convert_ingestion_input_to_blob(ingestion_input: IngestionInput) -> Blob:
    """Convert ingestion input to blob."""
    base64_file = ingestion_input["base64_file"]
    file_data = base64.decodebytes(base64_file.encode("utf-8"))
    mimetype = _guess_mimetype(file_data)
    filename = ingestion_input["filename"] if "filename" in ingestion_input else None
    return Blob.from_data(
        data=file_data,
        path=filename,
        mime_type=mimetype,
    )


class IngestRunnable(RunnableSerializable[IngestionInput, IngestionOutput]):
    text_splitter: TextSplitter
    vectorstore: VectorStore
    input_key: str
    namespace: str = ""

    class Config:
        arbitrary_types_allowed = True

    def invoke(
        self, input: IngestionInput, config: Optional[RunnableConfig] = None
    ) -> IngestionOutput:
        """Ingest a document into the vectorstore."""
        if not self.namespace:
            raise ValueError("namespace must be provided")

        docs = self.text_splitter.create_documents(
            [input[self.input_key]], [{"namespace": self.namespace}]
        )
        self.vectorstore.add_documents(docs)
        return {"success": True}

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


def ingest_blob(
    blob: Blob,
    parser: BaseBlobParser,
    text_splitter: TextSplitter,
    vectorstore: VectorStore,
    *,
    batch_size: int = 100,
) -> List[str]:
    """Ingest a document into the vectorstore."""
    docs_to_index = []
    ids = []
    for document in parser.lazy_parse(blob):
        docs_to_index.extend(text_splitter.split_documents([document]))
        if len(docs_to_index) >= batch_size:
            ids.extend(vectorstore.add_documents(docs_to_index))
            docs_to_index = []

    if len(docs_to_index) >= batch_size:
        ids.extend(vectorstore.add_documents(docs_to_index))

    return ids


async def aingest_blob(
    blob: Blob,
    parser: BaseBlobParser,
    text_splitter: TextSplitter,
    vectorstore: VectorStore,
    *,
    batch_size: int = 100,
) -> List[str]:
    """Async ingest a document into the vectorstore."""
    docs_to_index = []
    ids = []
    for document in parser.lazy_parse(blob):
        docs_to_index.extend(text_splitter.split_documents([document]))
        if len(docs_to_index) >= batch_size:
            ids.extend(vectorstore.add_documents(docs_to_index))
            docs_to_index = []

    if len(docs_to_index) >= batch_size:
        ids.extend(vectorstore.add_documents(docs_to_index))

    return ids
