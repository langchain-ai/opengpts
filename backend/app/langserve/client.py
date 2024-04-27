import sys
from typing import AsyncIterator, List, NamedTuple, Optional, Union

import httpx
import httpx_sse
from httpx._types import QueryParamTypes

from app.langserve.schema import (
    Assistant,
    Config,
    Metadata,
    Run,
    RunEvent,
    StreamMode,
    Thread,
)


def get_client(*, url: str = "http://localhost:8123") -> "LangServeClient":
    client = httpx.AsyncClient(
        base_url=url,
        transport=httpx.AsyncHTTPTransport(retries=5),
        timeout=httpx.Timeout(connect=5, read=60, write=60, pool=5),
    )
    return LangServeClient(client)


class StreamPart(NamedTuple):
    event: str
    data: dict


class LangServeClient:
    def __init__(self, client: httpx.AsyncClient) -> None:
        self.http = HttpClient(client)
        self.assistants = AssistantsClient(self.http)
        self.threads = ThreadsClient(self.http)
        self.runs = RunsClient(self.http)


class HttpClient:
    def __init__(self, client: httpx.AsyncClient) -> None:
        self.client = client

    async def get(self, path: str, *, params: QueryParamTypes = None) -> dict:
        """Make a GET request."""
        r = await self.client.get(path, params=params)
        try:
            r.raise_for_status()
        except httpx.HTTPStatusError as e:
            if sys.version_info >= (3, 11):
                e.add_note((await r.aread()).decode())
            raise e
        return r.json()

    async def post(self, path: str, *, json: dict) -> dict:
        """Make a POST request."""
        r = await self.client.post(path, json=json)
        try:
            r.raise_for_status()
        except httpx.HTTPStatusError as e:
            if sys.version_info >= (3, 11):
                e.add_note((await r.aread()).decode())
            raise e
        return r.json()

    async def put(self, path: str, *, json: dict) -> dict:
        """Make a PUT request."""
        r = await self.client.put(path, json=json)
        try:
            r.raise_for_status()
        except httpx.HTTPStatusError as e:
            if sys.version_info >= (3, 11):
                e.add_note((await r.aread()).decode())
            raise e
        return r.json()

    async def delete(self, path: str) -> None:
        """Make a DELETE request."""
        r = await self.client.delete(path)
        try:
            r.raise_for_status()
        except httpx.HTTPStatusError as e:
            if sys.version_info >= (3, 11):
                e.add_note((await r.aread()).decode())
            raise e

    async def stream(
        self, path: str, method: str, *, json: dict = None
    ) -> AsyncIterator[StreamPart]:
        """Stream the results of a request using SSE."""
        async with httpx_sse.aconnect_sse(self.client, method, path, json=json) as sse:
            try:
                sse.response.raise_for_status()
            except httpx.HTTPStatusError as e:
                if sys.version_info >= (3, 11):
                    e.add_note((await sse.response.aread()).decode())
                raise e
            async for event in sse.aiter_sse():
                yield StreamPart(event.event, event.json() if event.data else None)


class AssistantsClient:
    def __init__(self, http: HttpClient) -> None:
        self.http = http

    async def get(self, assistant_id: str) -> Assistant:
        """Get an assistant by ID."""
        return await self.http.get(f"/assistants/{assistant_id}")

    async def create(
        self,
        graph_id: Optional[str],
        config: Optional[Config] = None,
        *,
        metadata: Metadata = None,
    ) -> Assistant:
        """Create a new assistant."""
        return await self.http.post(
            "/assistants",
            json={"metadata": metadata, "graph_id": graph_id, "config": config or {}},
        )

    async def upsert(
        self,
        assistant_id: str,
        graph_id: str,
        config: Optional[Config] = None,
        *,
        metadata: Metadata = None,
    ) -> Assistant:
        """Create or update an assistant."""
        return await self.http.put(
            f"/assistants/{assistant_id}",
            json={"metadata": metadata, "graph_id": graph_id, "config": config or {}},
        )

    async def search(
        self, *, metadata: Metadata = None, limit: int = 10, offset: int = 0
    ) -> list[Assistant]:
        """Search for assistants."""
        return await self.http.post(
            "/assistants/search",
            json={"metadata": metadata, "limit": limit, "offset": offset},
        )


class ThreadsClient:
    def __init__(self, http: HttpClient) -> None:
        self.http = http

    async def get(self, thread_id: str) -> Thread:
        """Get a thread by ID."""
        return await self.http.get(f"/threads/{thread_id}")

    async def create(self, *, metadata: Metadata = None) -> Thread:
        """Create a new thread."""
        return await self.http.post("/threads", json={"metadata": metadata})

    async def upsert(self, thread_id: str, *, metadata: Metadata) -> Thread:
        """Create or update a thread."""
        return await self.http.put(f"/threads/{thread_id}", json={"metadata": metadata})

    async def delete(self, thread_id: str) -> None:
        """Delete a thread."""
        await self.http.delete(f"/threads/{thread_id}")

    async def search(
        self, *, metadata: Metadata = None, limit: int = 10, offset: int = 0
    ) -> list[Thread]:
        """Search for threads."""
        return await self.http.post(
            "/threads/search",
            json={"metadata": metadata, "limit": limit, "offset": offset},
        )

    async def get_state(self, thread_id: str) -> dict:
        """Get the state of a thread."""
        return await self.http.get(f"/threads/{thread_id}/state")

    async def update_state(self, thread_id: Union[str, Config], values: dict) -> None:
        """Update the state of a thread."""
        if isinstance(thread_id, dict):
            config = thread_id
            thread_id_: str = thread_id["configurable"]["thread_id"]
        else:
            thread_id_ = thread_id
            config = None
        return await self.http.post(
            f"/threads/{thread_id_}/state", json={"values": values, "config": config}
        )


class RunsClient:
    def __init__(self, http: HttpClient) -> None:
        self.http = http

    def stream(
        self,
        thread_id: str,
        assistant_id: str,
        *,
        input: Optional[dict] = None,
        stream_mode: StreamMode = "values",
        metadata: Optional[dict] = None,
        config: Optional[Config] = None,
        interrupt_before: Optional[list[str]] = None,
        interrupt_after: Optional[list[str]] = None,
    ) -> AsyncIterator[StreamPart]:
        """Create a run and stream the results."""
        return self.http.stream(
            f"/threads/{thread_id}/runs/stream",
            "POST",
            json={
                "input": input,
                "config": config,
                "metadata": metadata,
                "stream_mode": stream_mode,
                "assistant_id": assistant_id,
                "interrupt_before": interrupt_before,
                "interrupt_after": interrupt_after,
            },
        )

    async def create(
        self,
        thread_id: str,
        assistant_id: str,
        *,
        input: Optional[dict] = None,
        stream_mode: StreamMode = "values",
        metadata: Optional[dict] = None,
        config: Optional[Config] = None,
        interrupt_before: Optional[list[str]] = None,
        interrupt_after: Optional[list[str]] = None,
    ) -> Run:
        """Create a background run."""
        return await self.http.post(
            f"/threads/{thread_id}/runs",
            json={
                "input": input,
                "config": config,
                "metadata": metadata,
                "stream_mode": stream_mode,
                "assistant_id": assistant_id,
                "interrupt_before": interrupt_before,
                "interrupt_after": interrupt_after,
            },
        )

    async def list(
        self, thread_id: str, *, limit: int = 10, offset: int = 0
    ) -> List[Run]:
        """List runs."""
        return await self.http.get(f"/threads/{thread_id}/runs")

    async def get(self, thread_id: str, run_id: str) -> Run:
        """Get a run."""
        return await self.http.get(f"/threads/{thread_id}/runs/{run_id}")

    async def list_events(
        self, thread_id: str, run_id: str, *, limit: int = 10, offset: int = 0
    ) -> List[RunEvent]:
        """List run events."""
        return await self.http.get(f"/threads/{thread_id}/runs/{run_id}/events")
