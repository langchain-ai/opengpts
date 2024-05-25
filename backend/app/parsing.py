"""Module contains logic for parsing binary blobs into text."""
from langchain.text_splitter import MarkdownHeaderTextSplitter
from langchain_community.document_loaders.parsers import (
    BS4HTMLParser,
    PDFMinerParser,
)
from langchain_community.document_loaders.parsers.generic import MimeTypeBasedParser
from langchain_community.document_loaders.parsers.msword import MsWordParser
from langchain_community.document_loaders.parsers.txt import TextParser
from langchain_core.document_loaders import BaseBlobParser
from langchain_core.documents import Document


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
        splitter = MarkdownHeaderTextSplitter(headers_to_split_on)
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

MIMETYPE_BASED_PARSER = MimeTypeBasedParser(
    handlers=HANDLERS,
    fallback_parser=None,
)
