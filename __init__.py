from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import ui_router, db_router


def build_app():
    app = FastAPI(title='E2E-AI-CHATBOT')
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"]
    )
    app.include_router(ui_router)
    app.include_router(db_router)
    return app


app = build_app()
