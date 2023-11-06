from fastapi import FastAPI
from langserve import add_routes
from gizmo_agent import agent

app = FastAPI()

add_routes(app, agent, config_keys=["configurable"])

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8100)
