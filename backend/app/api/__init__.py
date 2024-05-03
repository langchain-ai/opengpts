from fastapi import APIRouter

from app.api.assistants import router as assistants_router
from app.api.runs import router as runs_router
from app.api.threads import router as threads_router

router = APIRouter()


@router.get("/ok")
async def ok():
    return {"ok": True}


router.include_router(
    assistants_router,
    prefix="/api/v1/assistants",
    tags=["assistants"],
)
router.include_router(
    runs_router,
    prefix="/api/v1/runs",
    tags=["runs"],
)
router.include_router(
    threads_router,
    prefix="/api/v1/threads",
    tags=["threads"],
)
