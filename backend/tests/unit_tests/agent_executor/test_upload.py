from io import BytesIO

from langchain.text_splitter import RecursiveCharacterTextSplitter
from fastapi import UploadFile
from app.upload import IngestRunnable, _guess_mimetype, convert_ingestion_input_to_blob
from tests.unit_tests.fixtures import get_sample_paths
from tests.unit_tests.utils import InMemoryVectorStore


def test_ingestion_runnable() -> None:
    """Test ingestion runnable"""
    vectorstore = InMemoryVectorStore()
    splitter = RecursiveCharacterTextSplitter()
    runnable = IngestRunnable(
        text_splitter=splitter,
        vectorstore=vectorstore,
        input_key="file_contents",
        assistant_id="TheParrot",
    )
    # Simulate file data
    file_data = BytesIO(b"test data")
    file_data.seek(0)
    # Create UploadFile object
    file = UploadFile(filename="testfile.txt", file=file_data)

    # Convert the file to blob
    blob = convert_ingestion_input_to_blob(file)
    ids = runnable.invoke(blob)
    assert len(ids) == 1


def test_mimetype_guessing() -> None:
    """Verify mimetype guessing for all fixtures."""
    name_to_mime = {}
    for file in sorted(get_sample_paths()):
        data = file.read_bytes()
        name_to_mime[file.name] = _guess_mimetype(file.name, data)

    assert {
        "sample.docx": (
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        ),
        "sample.epub": "application/epub+zip",
        "sample.html": "text/html",
        "sample.odt": "application/vnd.oasis.opendocument.text",
        "sample.pdf": "application/pdf",
        "sample.rtf": "application/rtf",
        "sample.txt": "text/plain",
    } == name_to_mime
