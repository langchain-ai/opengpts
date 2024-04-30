import asyncio
import logging
import os
from pathlib import Path

import orjson
from fastapi import FastAPI, Form, UploadFile
from fastapi.exceptions import HTTPException
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles


import app.storage as storage
from app.api import router as api_router
from app.auth.handlers import AuthedUser
from app.lifespan import lifespan
from app.upload import ingest_runnable


logger = logging.getLogger(__name__)

app = FastAPI(title="OpenGPTs API", lifespan=lifespan)


# Get root of app, used to point to directory containing static files
ROOT = Path(__file__).parent.parent


app.include_router(api_router)


@app.post("/ingest", description="Upload files to the given assistant.")
async def ingest_files(
    files: list[UploadFile], user: AuthedUser, config: str = Form(...)
) -> None:
    """Ingest a list of files."""
    config = orjson.loads(config)

    assistant_id = config["configurable"].get("assistant_id")
    if assistant_id is not None:
        assistant = await storage.get_assistant(user["user_id"], assistant_id)
        if assistant is None:
            raise HTTPException(status_code=404, detail="Assistant not found.")

    thread_id = config["configurable"].get("thread_id")
    if thread_id is not None:
        thread = await storage.get_thread(user["user_id"], thread_id)
        if thread is None:
            raise HTTPException(status_code=404, detail="Thread not found.")

    if config["configurable"].get("show_progress_bar"):
        ingest_runnable.abatch_as_completed([file.file for file in files], config)

        # The return type of the IngestRunnable is not compatible with the
        # FastAPI StreamingResponse (the data must have an `.encode()`
        # property). The results are (int, list) tuples, so lets use orjson to
        # byte the tuple
        async def decode_ingestion_response(ingest_generator):
            async for x in ingest_generator:
                yield orjson.dumps(x)
                await asyncio.sleep(3)  # Debug: to demonstrate streaming

        return StreamingResponse(
            decode_ingestion_response(
                ingest_runnable.abatch_as_completed(
                    [file.file for file in files], config
                )
            )
        )
    else:
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
