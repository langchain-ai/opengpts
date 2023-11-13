from pathlib import Path
from typing import Annotated, Optional

import orjson
from fastapi import Cookie, FastAPI, Form, Request, UploadFile
from fastapi.staticfiles import StaticFiles
from gizmo_agent import agent, ingest_runnable
from langchain.schema.runnable import RunnableConfig
from langserve import add_routes
from typing_extensions import TypedDict

from app.storage import (
    get_thread_messages,
    list_assistants,
    list_public_assistants,
    list_threads,
    put_assistant,
    put_thread,
)

app = FastAPI()

FEATURED_PUBLIC_ASSISTANTS = [
    "ba721964-b7e4-474c-b817-fb089d94dc5f",
    "dc3ec482-aafc-4d90-8a1a-afb9b2876cde",
]

# Get root of app, used to point to directory containing static files
ROOT = Path(__file__).parent.parent


def attach_user_id_to_config(
    config: RunnableConfig,
    request: Request,
) -> RunnableConfig:
    config["configurable"]["user_id"] = request.cookies["opengpts_user_id"]
    return config


add_routes(
    app,
    agent,
    config_keys=["configurable"],
    per_req_config_modifier=attach_user_id_to_config,
    enable_feedback_endpoint=True,
)


@app.post("/ingest")
def ingest_endpoint(files: list[UploadFile], config: str = Form(...)):
    config = orjson.loads(config)
    return ingest_runnable.batch([file.file for file in files], config)


@app.get("/assistants/")
def list_assistants_endpoint(opengpts_user_id: Annotated[str, Cookie()]):
    """List all assistants for the current user."""
    return list_assistants(opengpts_user_id)


@app.get("/assistants/public/")
def list_public_assistants_endpoint(shared_id: Optional[str] = None):
    return list_public_assistants(
        FEATURED_PUBLIC_ASSISTANTS + ([shared_id] if shared_id else [])
    )


class AssistantPayload(TypedDict):
    name: str
    config: dict
    public: bool


@app.put("/assistants/{aid}")
def put_assistant_endpoint(
    aid: str,
    payload: AssistantPayload,
    opengpts_user_id: Annotated[str, Cookie()],
):
    return put_assistant(
        opengpts_user_id,
        aid,
        name=payload["name"],
        config=payload["config"],
        public=payload["public"],
    )


@app.get("/threads/")
def list_threads_endpoint(opengpts_user_id: Annotated[str, Cookie()]):
    return list_threads(opengpts_user_id)


@app.get("/threads/{tid}/messages")
def get_thread_messages_endpoint(opengpts_user_id: Annotated[str, Cookie()], tid: str):
    return get_thread_messages(opengpts_user_id, tid)


class ThreadPayload(TypedDict):
    name: str
    assistant_id: str


@app.put("/threads/{tid}")
def put_thread_endpoint(
    opengpts_user_id: Annotated[str, Cookie()], tid: str, payload: ThreadPayload
):
    return put_thread(
        opengpts_user_id,
        tid,
        assistant_id=payload["assistant_id"],
        name=payload["name"],
    )


app.mount("", StaticFiles(directory=str(ROOT / "ui"), html=True), name="ui")

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8100)
