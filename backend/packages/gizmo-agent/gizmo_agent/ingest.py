from agent_executor.upload import IngestRunnable
import os
from langchain.vectorstores import Redis
from langchain.embeddings import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter

index_schema = {
    "tag": [{"name": "namespace"}],
}
vstore = Redis(
    redis_url=os.environ["REDIS_URL"],
    index_name="test1",
    embedding=OpenAIEmbeddings(),
    index_schema=index_schema
)

ingest_runnable = IngestRunnable(text_splitter=RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200), vectorstore=vstore, input_key="file_contents")
