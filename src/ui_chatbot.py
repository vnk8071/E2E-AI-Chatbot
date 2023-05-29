import gradio as gr

from llms import GPT4AllModel
from searchers import ElasticSearch
from loggers import AppLogger
from src.utils import (
    post_process_answer,
    post_process_code,
    reset_textbox,
    clear_history
    )
from src.functions import save_upload_file

logger = AppLogger().get_logger()
system_default = """You are GPT4All Assistant."""
server_error_msg = """**NETWORK ERROR DUE TO HIGH TRAFFIC. \
PLEASE REGENERATE OR REFRESH THIS PAGE.**"""
llm = GPT4AllModel(model_path="models/ggml-gpt4all-j-v1.3-groovy.bin")


def predict(
    system_content: str,
    question: str,
    index_name: str,
    server_host: str,
    model_type: str,
    model_path: str,
    chatbot: list = [],
    history: list = [],
):
    try:
        # Prepare the LLM and Elasticsearch
        global llm
        if model_path != "models/ggml-gpt4all-j-v1.3-groovy.bin":
            llm = GPT4AllModel(model_path=model_path)
        elif model_type != "GPT4All":
            logger.info(f"Model {model_type} not supported!")
        es = ElasticSearch(
            elasticsearch_host=f"{server_host}:9200",
            index_name=index_name
        )

        # Get the answer from the chain
        logger.info(f"Question: {question}")
        if len(question) >= 10:
            documents = es.simple_search(query=question)
            logger.info(f"Document: {documents}")
        else:
            documents = None
            logger.info("Simple question")
        answer = llm(
            system_content=system_content,
            question=question,
            context=documents
        )
        answer = post_process_code(answer)
        answer = post_process_answer(answer, documents, server_host)
        logger.info(f"Answer: {answer}")
        history.append(question)
        history.append(answer)
        chatbot = [(history[i], history[i + 1])
                   for i in range(0, len(history), 2)]
        return chatbot, history

    except Exception as e:
        logger.info(f"Question: {e}")
        answer = server_error_msg + " (error_code: 503)"
        logger.info(f"Answer: {answer}")
        history.append("")
        history.append(answer)
        chatbot = [(history[i], history[i + 1])
                   for i in range(0, len(history), 2)]
        return chatbot, history


title = """<h1 align="center">Chat with AI Chatbot🤖</h1>"""

with gr.Blocks(
    css="""
    footer .svelte-1lyswbr {display: none !important;}
    #col_container {margin-left: auto; margin-right: auto;}
    #chatbot .wrap.svelte-13f7djk {height: 70vh; max-height: 65vh}
    #chatbot .message.user.svelte-13f7djk.svelte-13f7djk \
    {width:fit-content; background:orange; border-bottom-right-radius:0}
    #chatbot .message.bot.svelte-13f7djk.svelte-13f7djk \
    {width:fit-content; padding-left: 16px; border-bottom-left-radius:0}
    #chatbot .pre {border:2px solid white;}
    pre {
    white-space: pre-wrap;       /* Since CSS 2.1 */
    white-space: -moz-pre-wrap;  /* Mozilla, since 1999 */
    white-space: -pre-wrap;      /* Opera 4-6 */
    white-space: -o-pre-wrap;    /* Opera 7 */
    word-wrap: break-word;       /* Internet Explorer 5.5+ */
    }
    """
) as demo:
    gr.HTML(title)
    with gr.Tab("Chatbot"):
        with gr.Row():
            with gr.Column(elem_id="col_container", scale=0.3):
                with gr.Accordion("Prompt", open=True):
                    system_content = gr.Textbox(
                        value=system_default,
                        show_label=False)
                with gr.Accordion("Config", open=True):
                    index_name = gr.Textbox(
                            value="document",
                            label="index_name"
                        )
                    server_host = gr.Textbox(
                            value="http://localhost",
                            label="server_host"
                        )
                    model_type = gr.Textbox(
                        value="GPT4All",
                        label="model_type"
                    )
                    model_path = gr.Textbox(
                        value="models/ggml-gpt4all-j-v1.3-groovy.bin",
                        label="model_path"
                    )

            with gr.Column(elem_id="col_container"):
                chatbot = gr.Chatbot(
                    elem_id="chatbot",
                    label="AI Chatbot 🤖"
                )
                question = gr.Textbox(
                    placeholder="Ask something",
                    show_label=False,
                    value=""
                )
                state = gr.State([])
                with gr.Row():
                    with gr.Column():
                        submit_btn = gr.Button(value="🚀 Send")
                    with gr.Column():
                        clear_btn = gr.Button(value="🗑️ Clear history")

        question.submit(
            predict,
            [
                system_content,
                question, index_name,
                server_host,
                model_type,
                model_path,
                chatbot,
                state
            ],
            [chatbot, state],
        )
        submit_btn.click(
            predict,
            [
                system_content,
                question, index_name,
                server_host,
                model_type,
                model_path,
                chatbot,
                state
            ],
            [chatbot, state],
        )
        submit_btn.click(reset_textbox, [], [question])
        clear_btn.click(clear_history, None, [chatbot, state, question])
        question.submit(reset_textbox, [], [question])
    with gr.Tab("Ingest"):
        server_host = gr.Textbox(
            value="http://localhost",
            label="server_host"
        )
        uploaded_files = gr.Files(file_count="multiple")
        logger.info(uploaded_files)
        js = "(x) => confirm('Please wait \
        some minutes for upload and ingest to db')"
        try:
            upload_btn = gr.Button(value="Upload & Ingest 🚀")
            upload_btn.click(
                fn=save_upload_file,
                inputs=[
                    uploaded_files,
                    server_host
                ],
                outputs=None,
                _js=js
            )
        except Exception:
            gr.Error("Check server host")

    demo.queue(
        concurrency_count=10,
        status_update_rate="auto"
    )


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--server-name", default="0.0.0.0")
    parser.add_argument("--server-port", default=8071)
    parser.add_argument("--share", action="store_true")
    parser.add_argument("--debug", action="store_true")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()
    demo.launch(
        server_name=args.server_name,
        server_port=args.server_port,
        share=args.share,
        debug=args.debug,
        ssl_verify=False
    )
