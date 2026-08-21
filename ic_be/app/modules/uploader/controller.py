import logging
from pathlib import Path

from fastapi import APIRouter, HTTPException
from starlette.responses import FileResponse

blob_router = APIRouter()

logger = logging.getLogger(__name__)
UPLOAD_DIR = "data"

# File Serving Router
@blob_router.get("/{path:path}")
async def get_file(path: str):

    file_path = Path(UPLOAD_DIR) / path

    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(file_path)
