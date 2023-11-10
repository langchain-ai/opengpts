from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from gizmo_agent import agent, ingest_runnable
from langserve import add_routes
from langchain.schema.runnable import RunnableConfig

from app.storage import (
    get_thread_messages,
    list_assistants,
    list_threads,
    put_assistant,
    put_thread,
)

app = FastAPI()


def attach_user_id_to_config(
    config: RunnableConfig, request: Request
) -> RunnableConfig:
    config["configurable"]["user_id"] = request.cookies["opengpts_user_id"]
    return config


add_routes(
    app,
    agent,
    config_keys=["configurable"],
    per_req_config_modifier=attach_user_id_to_config,
)

add_routes(
    app,
    ingest_runnable,
    config_keys=["configurable"],
    path="/ingest",
    per_req_config_modifier=attach_user_id_to_config,
)


@app.get("/assistants/")
def list_assistants_endpoint(req: Request):
    return list_assistants(req.cookies["opengpts_user_id"])


@app.put("/assistants/{aid}")
def put_assistant_endpoint(req: Request, aid: str, payload: dict):
    return put_assistant(
        req.cookies["opengpts_user_id"],
        aid,
        name=payload["name"],
        config=payload["config"],
    )


@app.get("/threads/")
def list_threads_endpoint(req: Request):
    return list_threads(req.cookies["opengpts_user_id"])


@app.get("/threads/{tid}/messages")
def get_thread_messages_endpoint(req: Request, tid: str):
    return get_thread_messages(req.cookies["opengpts_user_id"], tid)


@app.put("/threads/{tid}")
def put_thread_endpoint(req: Request, tid: str, payload: dict):
    return put_thread(
        req.cookies["opengpts_user_id"],
        tid,
        assistant_id=payload["assistant_id"],
        name=payload["name"],
    )


app.mount("", StaticFiles(directory="ui", html=True), name="ui")

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8100)
