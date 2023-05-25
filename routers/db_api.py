from fastapi import APIRouter
from fastapi.responses import FileResponse

db_router = APIRouter()


@db_router.get("/show-pdf/{pdf_path}")
async def read_pdf(pdf_path):
    return FileResponse(pdf_path)
