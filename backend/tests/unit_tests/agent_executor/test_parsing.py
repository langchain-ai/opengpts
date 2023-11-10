"""Test parsing logic."""
import mimetypes

from agent_executor.parsing import MIMETYPE_BASED_PARSER, SUPPORTED_MIMETYPES
from langchain.document_loaders import Blob

from tests.unit_tests.fixtures import get_sample_paths


def test_list_of_supported_mimetypes() -> None:
    """This list should generally grow! Protecting against typos in mimetypes."""
    assert SUPPORTED_MIMETYPES == [
        "application/msword",
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "text/html",
        "text/plain",
    ]


def test_attempt_to_parse_each_fixture() -> None:
    """Attempt to parse supported fixtures."""
    seen_mimetypes = set()
    for path in get_sample_paths():
        type_, _ = mimetypes.guess_type(path)
        if type_ not in SUPPORTED_MIMETYPES:
            continue
        seen_mimetypes.add(type_)
        blob = Blob.from_path(path)
        documents = MIMETYPE_BASED_PARSER.parse(blob)
        try:
            assert len(documents) == 1
            doc = documents[0]
            assert "source" in doc.metadata
            assert doc.metadata["source"] == str(path)
            assert "🦜" in doc.page_content
        except Exception as e:
            raise AssertionError(f"Failed to parse {path}") from e

    known_missing = {"application/msword"}
    assert set(SUPPORTED_MIMETYPES) - known_missing == seen_mimetypes
