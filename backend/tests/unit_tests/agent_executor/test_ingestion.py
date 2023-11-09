from agent_executor.upload import IngestRunnable
from langchain.text_splitter import RecursiveCharacterTextSplitter

from .utils import InMemoryVectorStore


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
    ids = runnable.invoke({"file_contents": "This is a test file."})
    assert len(ids) == 1
