import orjson
from fastapi import APIRouter, Form, HTTPException, UploadFile

import app.storage as storage
from app.api.assistants import router as assistants_router
from app.api.runs import router as runs_router
from app.api.threads import router as threads_router
from app.auth.handlers import AuthedUser
from app.upload import convert_ingestion_input_to_blob, ingest_runnable

router = APIRouter()


@router.post("/ingest", description="Upload files to the given assistant.")
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

    file_blobs = [convert_ingestion_input_to_blob(file) for file in files]
    return ingest_runnable.batch(file_blobs, config)


router.include_router(
    assistants_router,
    prefix="/assistants",
    tags=["assistants"],
)
router.include_router(
    runs_router,
    prefix="/runs",
    tags=["runs"],
)
router.include_router(
    threads_router,
    prefix="/threads",
    tags=["threads"],
)
