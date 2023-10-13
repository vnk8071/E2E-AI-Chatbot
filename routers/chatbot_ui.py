import gradio as gr

from config import settings
from llms import GPT4AllModel
from loggers import AppLogger
from memories import RedisMemory
from searchers import ElasticSearch
from src import (
    clear_history,
    post_process_answer,
    post_process_code,
    reset_textbox,
)

logger = AppLogger().get_logger()
llm = GPT4AllModel(model_path=settings.MODEL_PATH)


def predict(
    system_content: str,
    question: str,
    index_name: str,
    server_host: str,
    model_type: str,
    model_path: str,
    chatbot: list,
    history: list,
):
    try:
        # Prepare the LLM and Elasticsearch
        global llm
        if model_path != settings.MODEL_PATH:
            llm = GPT4AllModel(model_path=model_path)
        elif model_type != "GPT4All":
            logger.info(f"Model {model_type} not supported!")
        es = ElasticSearch(
            elasticsearch_host=f"{server_host}:9200", index_name=index_name
        )
        redis_memory = RedisMemory(session_id="chatbot")

        # Get the answer from the chain
        logger.info(f"Question: {question}")
        if len(question) >= 20:
            documents = es.simple_search(query=question)
            logger.info(f"Document: {documents}")
        else:
            documents = None
            logger.info("Simple question")

        answer_from_redis = redis_memory.get_answer(question)
        if answer_from_redis:
            history.append(question)
            history.append(answer_from_redis)
            chatbot = [(history[i], history[i + 1]) for i in range(0, len(history), 2)]
            return chatbot, history

        answer = llm(
            system_content=system_content, question=question, context=documents
        )
        answer = post_process_code(answer)
        answer = post_process_answer(answer, documents, server_host)
        logger.info(f"Answer: {answer}")
        redis_memory.add_chat_history(question, answer)
        history.append(question)
        history.append(answer)
        chatbot = [(history[i], history[i + 1]) for i in range(0, len(history), 2)]
        return chatbot, history

    except Exception as e:
        logger.info(f"Question: {e}")
        answer = settings.SERVER_ERROR_MSG + " (error_code: 503)"
        logger.info(f"Answer: {answer}")
        history.append(question)
        history.append(answer)
        chatbot = [(history[i], history[i + 1]) for i in range(0, len(history), 2)]
        return chatbot, history


title = """
<h1 align="center">Chat with AI Chatbot 🤖</h1>
"""
current_version = "2.0.0"
version = f"""
- Version 1.0.0: Pipeline with GPT4All, Elasticsearch, MongoDB and Gradio
- Version {current_version}: Add Redis Memory, Version, Login, and change User Interface
"""

with gr.Blocks(
    css="""
    footer .svelte-1ax1toq {display: none !important;}
    #col_container {margin-left: auto; margin-right: auto;}
    #chatbot .block.svelte-90oupt {height:600px;}
    #chatbot .message.user.svelte-1pjfiar.svelte-1pjfiar \
    {width:fit-content; background:orange; border-bottom-right-radius:0}
    #chatbot .message.bot.svelte-1pjfiar.svelte-1pjfiar \
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
) as chatbot_router:
    gr.HTML(value=title)
    with gr.Row():
        with gr.Column(elem_id="col_container", scale=1):
            with gr.Accordion(label="Prompt", open=True):
                system_content = gr.Textbox(
                    value=settings.SYSTEM_DEFAULT, show_label=False
                )
            with gr.Accordion(label="Config", open=True):
                index_name = gr.Textbox(value=settings.INDEX_NAME, label="index_name")
                server_host = gr.Textbox(
                    value=settings.SERVER_HOST, label="server_host"
                )
                model_type = gr.Textbox(value=settings.MODEL_TYPE, label="model_type")
                model_path = gr.Textbox(value=settings.MODEL_PATH, label="model_path")

        with gr.Column(elem_id="col_container", scale=3):
            inital_chat = ["👋", "Hi user, I'm an AI Assistant 🤖 trained from GPT4ALL!"]
            chatbot = gr.Chatbot(
                value=[inital_chat],
                elem_id="chatbot",
                label=f"AI Chatbot 🤖 - version {current_version}",
            )
            question = gr.Textbox(
                placeholder="Ask something", show_label=False, value=""
            )
            state = gr.State(inital_chat)
            with gr.Row():
                with gr.Column():
                    submit_btn = gr.Button(value="🚀 Send")
                with gr.Column():
                    clear_btn = gr.Button(value="🗑️ Clear history")

    gr.HTML(value="<h3>📋 Services User Interface</h3>")
    with gr.Row():
        with gr.Column():
            gr.Button(value="Ingest Database", link="/show-ingest")
        with gr.Column():
            gr.Button(value="Mongo Express", link="/mongoexpress")
        with gr.Column():
            gr.Button(value="Elastic Search", link="/elasticsearch")
        with gr.Column():
            gr.Button(value="Kibana", link="/kibana")

    gr.Markdown(version)

    question.submit(
        predict,
        [
            system_content,
            question,
            index_name,
            server_host,
            model_type,
            model_path,
            chatbot,
            state,
        ],
        [chatbot, state],
    )
    submit_btn.click(
        predict,
        [
            system_content,
            question,
            index_name,
            server_host,
            model_type,
            model_path,
            chatbot,
            state,
        ],
        [chatbot, state],
    )
    submit_btn.click(reset_textbox, [], [question])
    clear_btn.click(clear_history, None, [chatbot, state, question])
    question.submit(reset_textbox, [], [question])


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--server-name", default="0.0.0.0")
    parser.add_argument("--server-port", default=8071)
    parser.add_argument("--share", action="store_true")
    parser.add_argument("--debug", action="store_true")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()
    chatbot_router.launch(
        server_name=args.server_name,
        server_port=args.server_port,
        share=args.share,
        debug=args.debug,
        ssl_verify=False,
    )
