import os
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI
from langgraph_sdk.client import LangGraphClient, get_client

_langserve = None


def get_api_client() -> LangGraphClient:
    return _langserve


@asynccontextmanager
async def lifespan(app: FastAPI):
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.UnicodeDecoder(),
            structlog.stdlib.render_to_log_kwargs,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    global _langserve

    _langserve = get_client(url=os.environ["LANGGRAPH_URL"])
    yield
    await _langserve.http.client.aclose()
    _langserve = None
