from fastapi import APIRouter
from starlette.responses import RedirectResponse

ui_router = APIRouter()


@ui_router.get("/elasticsearch")
async def route_elasticsearch():
    return RedirectResponse(url="http://localhost:9200/")


@ui_router.get("/kibana")
async def route_kibana():
    return RedirectResponse(url="http://localhost:5601/")


@ui_router.get("/mongodb")
async def route_mongodb():
    return RedirectResponse(url="http://localhost:27017/")
