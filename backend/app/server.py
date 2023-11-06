from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from langserve import add_routes
from gizmo_agent import agent

app = FastAPI()

add_routes(app, agent, config_keys=["configurable"])

app.mount("", StaticFiles(directory="ui", html=True), name="ui")

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8100)
