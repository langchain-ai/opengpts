import os
from pathlib import Path
from typing import Any, MutableMapping

import httpx
import structlog
from fastapi import FastAPI
from fastapi.exception_handlers import http_exception_handler
from fastapi.exceptions import HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from starlette.responses import Response

from app.api import router as api_router
from app.lifespan import lifespan

logger = structlog.get_logger(__name__)

app = FastAPI(title="OpenGPTs API", lifespan=lifespan)


@app.exception_handler(httpx.HTTPStatusError)
async def httpx_http_status_error_handler(request, exc: httpx.HTTPStatusError):
    return await http_exception_handler(
        request, HTTPException(status_code=exc.response.status_code, detail=str(exc))
    )


# Get root of app, used to point to directory containing static files
ROOT = Path(__file__).parent.parent


@app.get("/ok")
async def ok():
    return {"ok": True}


app.include_router(api_router, prefix="/api")


ui_dir = str(ROOT / "ui")


class StaticFilesSpa(StaticFiles):
    async def get_response(
        self, path: str, scope: MutableMapping[str, Any]
    ) -> Response:
        res = await super().get_response(path, scope)
        if isinstance(res, FileResponse) and res.status_code == 404:
            res.status_code = 200
        return res


if os.path.exists(ui_dir):
    app.mount("", StaticFilesSpa(directory=ui_dir, html=True), name="ui")
else:
    logger.warn("No UI directory found, serving API only.")

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8100)
