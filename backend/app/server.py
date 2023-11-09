from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from langserve import add_routes
from gizmo_agent import agent, ingest_runnable

from app.storage import list_assistants, put_assistant, list_threads, put_thread

app = FastAPI()

add_routes(app, agent, config_keys=["configurable"])

add_routes(app, ingest_runnable, config_keys=["configurable"], path="/ingest")


@app.get("/assistants/")
def list_assistants_endpoint():
    return list_assistants()


@app.put("/assistants/{aid}")
def put_assistant_endpoint(aid: str, name: str, config: dict):
    return put_assistant(aid, name, config)


@app.get("/assistants/{aid}/threads/")
def list_threads_endpoint(aid: str):
    return list_threads(aid)


@app.put("/assistants/{aid}/threads/{tid}")
def put_thread_endpoint(aid: str, tid: str, name: str):
    return put_thread(aid, tid, name)


app.mount("", StaticFiles(directory="ui", html=True), name="ui")

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8100)
