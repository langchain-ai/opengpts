import os

from agent_executor.upload import IngestRunnable
from langchain.embeddings import OpenAIEmbeddings
from langchain.schema.runnable import ConfigurableField
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores.redis import Redis

index_schema = {
    "tag": [{"name": "namespace"}],
}
vstore = Redis(
    redis_url="redis://redis-10437.c28195.us-central1-1.gcp.cloud.rlrcp.com:10437/0?password=EKT7BrnAWBoPmRbENx3R76h9yII6DSHZ",
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
