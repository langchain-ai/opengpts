from agent_executor.upload import IngestRunnable, _guess_mimetype
from langchain.text_splitter import RecursiveCharacterTextSplitter

from tests.unit_tests.fixtures import get_sample_paths
from tests.unit_tests.utils import InMemoryVectorStore
import base64


def _create_file_contents(content: str) -> str:
    """Create file contents."""
    # lots of overhead here so that it can be passed as JSON...
    return base64.b64encode(content.encode("utf-8")).decode("utf-8")


def test_ingestion_runnable() -> None:
    """Test ingestion runnable"""
    vectorstore = InMemoryVectorStore()
    splitter = RecursiveCharacterTextSplitter()
    runnable = IngestRunnable(
        text_splitter=splitter,
        vectorstore=vectorstore,
        input_key="file_contents",
        namespace="test1",
    )
    ids = runnable.invoke(
        {"file_contents": _create_file_contents("This is a test file.")}
    )
    assert len(ids) == 1


def test_mimetype_guessing() -> None:
    """Verify mimetype guessing for all fixtures."""
    name_to_mime = {}
    for file in sorted(get_sample_paths()):
        data = file.read_bytes()
        name_to_mime[file.name] = _guess_mimetype(data)

    assert {
        "sample.docx": (
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        ),
        "sample.epub": "application/epub+zip",
        "sample.html": "text/html",
        "sample.odt": "application/vnd.oasis.opendocument.text",
        "sample.pdf": "application/pdf",
        "sample.rtf": "text/rtf",
        "sample.txt": "text/plain",
    } == name_to_mime
