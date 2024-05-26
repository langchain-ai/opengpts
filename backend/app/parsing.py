"""Module contains logic for parsing binary blobs into text."""
from typing import Iterator, Mapping, Optional

from langchain.text_splitter import MarkdownHeaderTextSplitter
from langchain_community.document_loaders.parsers import (
    BS4HTMLParser,
    PDFMinerParser,
)
from langchain_community.document_loaders.parsers.msword import MsWordParser
from langchain_community.document_loaders.parsers.txt import TextParser
from langchain_core.document_loaders import BaseBlobParser
from langchain_core.document_loaders.blob_loaders import Blob
from langchain_core.documents import Document


class MimeTypeParser(BaseBlobParser):
    """Parser that uses `mime`-types to parse a blob.

    This parser is useful for simple pipelines where the mime-type is sufficient
    to determine how to parse a blob.

    To use, configure handlers based on mime-types and pass them to the initializer.

    Example:

        .. code-block:: python

        from langchain_community.document_loaders.parsers.generic import MimeTypeBasedParser

        parser = MimeTypeBasedParser(
            handlers={
                "application/pdf": ...,
            },
            fallback_parser=...,
        )
    """  # noqa: E501

    def __init__(
        self,
        handlers: Mapping[str, BaseBlobParser],
        *,
        fallback_parser: Optional[BaseBlobParser] = None,
    ) -> None:
        """Define a parser that uses mime-types to determine how to parse a blob.

        Args:
            handlers: A mapping from mime-types to functions that take a blob, parse it
                      and return a document.
            fallback_parser: A fallback_parser parser to use if the mime-type is not
                             found in the handlers. If provided, this parser will be
                             used to parse blobs with all mime-types not found in
                             the handlers.
                             If not provided, a ValueError will be raised if the
                             mime-type is not found in the handlers.
        """
        self.handlers = handlers
        self.fallback_parser = fallback_parser

    def lazy_parse(self, blob: Blob) -> Iterator[Document]:
        """Load documents from a blob."""
        mimetype = blob.mimetype

        if mimetype is None:
            if blob.path.name.endswith(".md"):
                mimetype = "text/markdown"
            else:
                raise ValueError(f"{blob} does not have a mimetype.")

        if mimetype in self.handlers:
            handler = self.handlers[mimetype]
            yield from handler.lazy_parse(blob)
        else:
            if self.fallback_parser is not None:
                yield from self.fallback_parser.lazy_parse(blob)
            else:
                raise ValueError(f"Unsupported mime type: {mimetype}")


class MarkdownParser(BaseBlobParser):
    """Parser for Markdown blobs."""

    def lazy_parse(self, blob: Blob) -> Iterator[Document]:  # type: ignore[valid-type]
        """Lazily parse the blob."""
        headers_to_split_on = [
            ("#", "Header 1"),
            ("##", "Header 2"),
            ("###", "Header 3"),
            ("###$", "Header 4"),
            ("####", "Header 5"),
            ("#####", "Header 6"),
        ]
        splitter = MarkdownHeaderTextSplitter(
            headers_to_split_on, return_each_line=True
        )
        for doc in splitter.split_text(blob.as_string()):
            yield doc


HANDLERS = {
    "application/pdf": PDFMinerParser(),
    "text/plain": TextParser(),
    "text/markdown": MarkdownParser(),
    "text/html": BS4HTMLParser(),
    "application/msword": MsWordParser(),
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": (
        MsWordParser()
    ),
}

SUPPORTED_MIMETYPES = sorted(HANDLERS.keys())

# PUBLIC API

MIMETYPE_BASED_PARSER = MimeTypeParser(
    handlers=HANDLERS,
    fallback_parser=None,
)
