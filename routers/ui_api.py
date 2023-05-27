from fastapi import APIRouter
from starlette.responses import RedirectResponse

from loggers import AppLogger

logger = AppLogger().get_logger()
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


@ui_router.get("/mongoexpress")
async def route_mongo_express():
    return RedirectResponse(url="http://localhost:8081/")
