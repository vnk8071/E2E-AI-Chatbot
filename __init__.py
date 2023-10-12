from fastapi import FastAPI, staticfiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles


def build_app():
    app = FastAPI(title="E2E-AI-CHATBOT")
    app.mount("/static", StaticFiles(directory="static"), name="static")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    return app


app = build_app()
