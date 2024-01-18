from fastapi import APIRouter

from app.api.assistants import router as assistants_router
from app.api.runs import router as runs_router
from app.api.threads import router as threads_router

router = APIRouter()

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
