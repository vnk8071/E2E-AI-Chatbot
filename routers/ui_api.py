from fastapi import APIRouter
from starlette.responses import RedirectResponse

from config import settings
from loggers import AppLogger

logger = AppLogger().get_logger()
ui_router = APIRouter()


@ui_router.get("/elasticsearch")
async def route_elasticsearch():
    return RedirectResponse(url=settings.SERVER_HOST + ":9200/")


@ui_router.get("/kibana")
async def route_kibana():
    return RedirectResponse(url=settings.SERVER_HOST + ":5601/")


@ui_router.get("/mongodb")
async def route_mongodb():
    return RedirectResponse(url=settings.SERVER_HOST + ":27017/")


@ui_router.get("/mongoexpress")
async def route_mongo_express():
    return RedirectResponse(url=settings.SERVER_HOST + ":8081/")


@ui_router.get("/website")
async def route_website():
    return RedirectResponse(url="https://khoivn.space/")
