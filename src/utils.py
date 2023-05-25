import gradio as gr


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
    try:
        source = metadata["source"]
        page = metadata["page"]
        url_pdf = f"{server_host}/show-pdf/{source}"
        if source:
            answer += f"<br><br>Source: <a href='{url_pdf}'>{source}#page={page}</a>"
    finally:
        answer = answer.replace("\n", "<br>")
        return answer


def reset_textbox():
    return gr.update(value="")
