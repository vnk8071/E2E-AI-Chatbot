import gradio as gr

from src import demo
from __init__ import app

gr.mount_gradio_app(app, demo, "/")


if __name__ == '__main__':
    import uvicorn
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", default=8071)
    args = parser.parse_args()
    uvicorn.run(
        app=app,
        host="0.0.0.0",
        port=8071
    )
