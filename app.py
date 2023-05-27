import gradio as gr

import uvicorn
import argparse
from src import demo
from __init__ import app
from loggers import AppLogger

parser = argparse.ArgumentParser()
parser.add_argument(
    "--host",
    default="0.0.0.0",
    type=str
)
parser.add_argument(
    "--port",
    default=8071,
    type=int
)
args = parser.parse_args()
logger = AppLogger().get_logger()


@app.on_event("startup")
async def startup_event():
    gr.mount_gradio_app(app, demo, "/")
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


if __name__ == '__main__':
    uvicorn.run(
        app=app,
        host=args.host,
        port=args.port
    )
