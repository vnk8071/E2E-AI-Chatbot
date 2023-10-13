from pydantic import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "End-to-End AI Chatbot"
    USERNAME = "admin"
    PASSWORD = "admin"
    HOST = "0.0.0.0"
    PORT = 8071

    # Config GPT4ALL model
    MODEL_PATH = "models/ggml-gpt4all-j-v1.3-groovy.bin"
    MODEL_TYPE = "GPT4All"
    SERVER_HOST = "http://localhost"
    INDEX_NAME = "document"
    SYSTEM_DEFAULT = (
        """You are GPT4All Assistant help to answer questions about private document."""
    )
    SERVER_ERROR_MSG = """**NETWORK ERROR DUE TO HIGH TRAFFIC. PLEASE REGENERATE OR REFRESH THIS PAGE.**"""

    # Config database
    DATA_PATH = "static/pdf/"


settings = Settings()
