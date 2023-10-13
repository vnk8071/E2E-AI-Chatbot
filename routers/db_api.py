import gradio as gr
from fastapi import APIRouter

from loggers import AppLogger
from src import save_upload_file, ingest_database, ingest_search

logger = AppLogger().get_logger()
db_router = APIRouter()


def upload_file(files):
    file_paths = [file.name for file in files]
    return file_paths


def ingest_process(files):
    try:
        save_upload_file(uploaded_files=files)
        ingest_database(database_name="document")
        ingest_search(index_name="document")
        return "Done"
    except Exception as e:
        logger.info("Please check server host")
        logger.error(f"Exception: {e}")


with gr.Blocks() as ingest_router:
    gr.HTML(value="""<h1 align="center">Ingest with AI Chatbot 🤖</h1>""")
    uploaded_file = gr.Files(file_types=[".pdf"])

    text_output = gr.Textbox(label="Ingest Status", default_text="")
    text_button = gr.Button("🚀 Start Ingest")
    text_button.click(ingest_process, uploaded_file, text_output)
