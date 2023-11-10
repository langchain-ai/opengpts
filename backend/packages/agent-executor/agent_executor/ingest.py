"""Code to ingest blob into a vectorstore.

Code is responsible for taking binary data, parsing it and then indexing it
into a vector store.

This code should be agnostic to how the blob got generated; i.e., it does not
know about server/uploading etc.
"""
from typing import List

from langchain.document_loaders import Blob
from langchain.document_loaders.base import BaseBlobParser
from langchain.schema import Document
from langchain.schema.vectorstore import VectorStore
from langchain.text_splitter import TextSplitter


def _update_document_metadata(document: Document, namespace: str) -> None:
    """Mutation in place that adds a namespace to the document metadata."""
    document.metadata["namespace"] = namespace


# PUBLIC API


def ingest_blob(
    blob: Blob,
    parser: BaseBlobParser,
    text_splitter: TextSplitter,
    vectorstore: VectorStore,
    namespace: str,
    *,
    batch_size: int = 100,
) -> List[str]:
    """Ingest a document into the vectorstore."""
    docs_to_index = []
    ids = []
    for document in parser.lazy_parse(blob):
        docs = text_splitter.split_documents([document])
        for doc in docs:
            _update_document_metadata(doc, namespace)
        docs_to_index.extend(docs)

        if len(docs_to_index) >= batch_size:
            ids.extend(vectorstore.add_documents(docs_to_index))
            docs_to_index = []

    if docs_to_index:
        ids.extend(vectorstore.add_documents(docs_to_index))

    return ids
