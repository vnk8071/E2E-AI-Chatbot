import gradio as gr

from loggers import AppLogger

logger = AppLogger().get_logger()


def clear_history():
    state = None
    return ([], state, "")


def post_process_code(code):
    sep = "\n```"
    if sep in code:
        blocks = code.split(sep)
        if len(blocks) % 2 == 1:
            for i in range(1, len(blocks), 2):
                blocks[i] = blocks[i].replace("\\_", "_")
        code = sep.join(blocks)
    return code


def post_process_answer(answer, metadata=None, server_host=None):
    if metadata is not None:
        source = metadata[0].metadata["source"]
        page = metadata[0].metadata["page"]
        path = f"{source}#page={page}"
        url_pdf = f"{server_host}/static/pdf/{path}"
        answer += f"<br><br>Source: <a href='{url_pdf}' _target='blank'>{path}</a>"
    answer = answer.replace("\n", "<br>")
    return answer


def reset_textbox():
    return gr.update(value="")
