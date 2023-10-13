import argparse
import mimetypes
import secrets
import shutil
import fastapi
import gradio as gr
import uvicorn
from fastapi import Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import (
    FileResponse,
    HTMLResponse,
    JSONResponse,
    PlainTextResponse,
)
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.templating import Jinja2Templates
from importlib_resources import files
from starlette.responses import RedirectResponse, StreamingResponse

from __init__ import app
from config import settings
from loggers import AppLogger
from route_utils import safe_join, strip_url
from routers import db_router, ui_router, chatbot_router, ingest_router

parser = argparse.ArgumentParser()
parser.add_argument("--host", default=settings.HOST, type=str)
parser.add_argument("--port", default=settings.PORT, type=int)
args = parser.parse_args()
logger = AppLogger().get_logger()
templates = Jinja2Templates(directory="templates")
TOKEN = secrets.token_urlsafe(16)
STATIC_PATH_LIB = files("gradio").joinpath("templates", "frontend", "static").as_posix()  # type: ignore
BUILD_PATH_LIB = files("gradio").joinpath("templates", "frontend", "assets").as_posix()  # type: ignore


@app.on_event("startup")
async def startup_event():
    app.auth = (settings.USERNAME, settings.PASSWORD)
    app.tokens = {}
    app.log_in = False
    logger.info("Starting up...")
    logger.info(f"Host: {args.host}")
    logger.info(f"Port: {args.port}")
    if args.host == "0.0.0.0":
        logger.info(f"Access URL: http://localhost:{args.port}")
    else:
        logger.info(f"Access URL: http://{args.host}:{args.port}")


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down...")


@app.get("/user")
def get_current_user(request: fastapi.Request):
    token = request.cookies.get("access-token") or request.cookies.get(
        "access-token-unsecure"
    )
    logger.info(f"token: {token}")
    return app.tokens.get(token)


@app.get("/login_check")
def login_check(user: str = Depends(get_current_user)):
    if app.auth is None or user is not None:
        return
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated"
    )


@app.head("/", response_class=HTMLResponse)
@app.get("/", response_class=HTMLResponse)
def main(request: fastapi.Request):
    if app.log_in:
        return RedirectResponse("/show-app")
    mimetypes.add_type("application/javascript", ".js")

    return templates.TemplateResponse(
        "frontend/index.html",
        {"request": request},
    )


@app.get("/show-app", dependencies=[Depends(login_check)])
async def show(user: str = Depends(get_current_user)):
    gr.mount_gradio_app(app, chatbot_router, "/chat/")
    return RedirectResponse("/chat/")


@app.get("/show-ingest", dependencies=[Depends(login_check)])
async def ingest_page():
    gr.mount_gradio_app(app, ingest_router, "/ingest/")
    return RedirectResponse("/ingest/")


@app.get("/token")
def get_token(request: fastapi.Request) -> dict:
    token = request.cookies.get("access-token")
    return {"token": token, "user": app.tokens.get(token)}


@app.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    username, password = form_data.username.strip(), form_data.password
    if username == settings.USERNAME and password == settings.PASSWORD:
        token = TOKEN
        app.tokens[token] = username
        app.log_in = True
        response = JSONResponse(content={"success": True})
        response.set_cookie(
            key="access-token",
            value=token,
            httponly=True,
            samesite="none",
            secure=True,
        )
        response.set_cookie(
            key="access-token-unsecure",
            value=token,
            httponly=True,
        )
        logger.info(f"response: {response}")
        return response
    else:
        raise HTTPException(status_code=400, detail="Incorrect credentials.")


@app.get("/config", dependencies=[Depends(login_check)])
def get_config(request: fastapi.Request):
    root_path = (
        request.scope.get("root_path") or request.headers.get("X-Direct-Url") or ""
    )
    config = app.get_blocks().config
    config["root"] = strip_url(root_path)
    return config


@app.get("/static/{path:path}")
def static_resource(path: str):
    static_file = safe_join(STATIC_PATH_LIB, path)
    return FileResponse(static_file)


@app.get("/assets/{path:path}")
def build_resource(path: str):
    build_file = safe_join(BUILD_PATH_LIB, path)
    return FileResponse(build_file)


@app.get("/favicon.ico")
async def favicon():
    return static_resource("img/logo.svg")


@app.get("/theme.css", response_class=PlainTextResponse)
def theme_css():
    return PlainTextResponse(
        gr.themes.Default()._get_theme_css(), media_type="text/css"
    )


app.include_router(router=ui_router, dependencies=[Depends(login_check)])
app.include_router(router=db_router, dependencies=[Depends(login_check)])


if __name__ == "__main__":
    uvicorn.run(app=app, host=args.host, port=args.port)
