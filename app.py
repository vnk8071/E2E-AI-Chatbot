import gradio as gr

from src import demo
from __init__ import app

gr.mount_gradio_app(app, demo, "/")


if __name__ == '__main__':
    import uvicorn
    uvicorn.run(
        app=app,
        host="0.0.0.0",
        port="8071"
    )
