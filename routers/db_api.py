import shutil
from fastapi import (
    APIRouter,
    UploadFile,
    )
from fastapi.responses import (
    HTMLResponse
)

from loggers import AppLogger

logger = AppLogger().get_logger()
db_router = APIRouter()


@db_router.get("/ingest")
async def ingest_page():
    content = """
<body>
<form action="/ingest" enctype="multipart/form-data" method="post">
<input name="files" type="file" multiple>
<input type="submit">
</form>
</body>
    """
    return HTMLResponse(content=content)


@db_router.post("/ingest")
async def create_ingest(file: UploadFile):
    try:
        dest_path = f"samples/{file.filename}"
        logger.info(f"dest_path {dest_path}")
        with dest_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    finally:
        file.file.close()
