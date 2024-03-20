import logging
import os
from pathlib import Path

import orjson
from fastapi import FastAPI, Form, UploadFile
from fastapi.staticfiles import StaticFiles

from app.api import router as api_router
from app.lifespan import lifespan
from app.upload import ingest_runnable

logger = logging.getLogger(__name__)

app = FastAPI(title="OpenGPTs API", lifespan=lifespan)


# Get root of app, used to point to directory containing static files
ROOT = Path(__file__).parent.parent


app.include_router(api_router)


@app.post("/ingest", description="Upload files to the given assistant.")
def ingest_files(files: list[UploadFile], config: str = Form(...)) -> None:
    """Ingest a list of files."""
    config = orjson.loads(config)
    return ingest_runnable.batch([file.file for file in files], config)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}


ui_dir = str(ROOT / "ui")

if os.path.exists(ui_dir):
    app.mount("", StaticFiles(directory=ui_dir, html=True), name="ui")
else:
    logger.warn("No UI directory found, serving API only.")

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8100)
