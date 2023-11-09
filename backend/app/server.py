from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from gizmo_agent import agent, ingest_runnable
from langserve import add_routes

from app.storage import (
    get_thread_messages,
    list_assistants,
    list_threads,
    put_assistant,
    put_thread,
)

app = FastAPI()

add_routes(app, agent, config_keys=["configurable"])

add_routes(app, ingest_runnable, config_keys=["configurable"], path="/ingest")


@app.get("/assistants/")
def list_assistants_endpoint():
    return list_assistants()


@app.put("/assistants/{aid}")
def put_assistant_endpoint(aid: str, payload: dict):
    return put_assistant(aid, name=payload["name"], config=payload["config"])


@app.get("/threads/")
def list_threads_endpoint():
    return list_threads()


@app.get("/threads/{tid}/messages")
def get_thread_messages_endpoint(tid: str):
    return get_thread_messages(tid)


@app.put("/threads/{tid}")
def put_thread_endpoint(tid: str, payload: dict):
    return put_thread(tid, assistant_id=payload["assistant_id"], name=payload["name"])


app.mount("", StaticFiles(directory="ui", html=True), name="ui")

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8100)
