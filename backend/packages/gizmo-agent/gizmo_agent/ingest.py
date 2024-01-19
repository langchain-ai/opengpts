import os

from agent_executor.upload import IngestRunnable
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores.redis import Redis
from langchain_core.runnables import ConfigurableField

index_schema = {
    "tag": [{"name": "namespace"}],
}
vstore = Redis(
    redis_url=os.environ["REDIS_URL"],
    index_name="opengpts",
    embedding=OpenAIEmbeddings(),
    index_schema=index_schema,
)


ingest_runnable = IngestRunnable(
    text_splitter=RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200),
    vectorstore=vstore,
).configurable_fields(
    assistant_id=ConfigurableField(
        id="assistant_id",
        annotation=str,
        name="Assistant ID",
    ),
)
