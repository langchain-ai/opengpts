from pathlib import Path

import orjson
from fastapi import FastAPI, Form, UploadFile
from fastapi.staticfiles import StaticFiles
from gizmo_agent import ingest_runnable

from app.api import router as api_router

app = FastAPI(title="OpenGPTs API")


# Get root of app, used to point to directory containing static files
ROOT = Path(__file__).parent.parent


app.include_router(api_router)


@app.post("/ingest", description="Upload files to the given assistant.")
def ingest_files(files: list[UploadFile], config: str = Form(...)) -> None:
    """Ingest a list of files."""
    config = orjson.loads(config)
    return ingest_runnable.batch([file.file for file in files], config)


app.mount("", StaticFiles(directory=str(ROOT / "ui"), html=True), name="ui")

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8100)
