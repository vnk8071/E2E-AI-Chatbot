import shutil

from fastapi import APIRouter, File, UploadFile
from fastapi.responses import HTMLResponse

from loggers import AppLogger

logger = AppLogger().get_logger()
db_router = APIRouter()


@db_router.get("/ingest")
async def ingest_page():
    content = """
<head>
    <meta charset="utf-8" />
    <meta
        name="viewport"
        content="width=device-width, initial-scale=1, shrink-to-fit=no, maximum-scale=1"
    />

    <meta property="og:url" content="https://gradio.app/" />
    <meta property="og:type" content="website" />
    <meta property="og:image" content="" />
    <meta property="og:title" content="" />
    <meta
        property="og:description"
        content=""
    />
    <meta name="twitter:card" content="summary_large_image" />
    <meta name="twitter:creator" content="@teamGradio" />
    <meta name="twitter:title" content="" />
    <meta
        name="twitter:description"
        content=""
    />
    <meta name="twitter:image" content="" />

    <script>
        window.__gradio_mode__ = "app";
    </script>

    <script>window.gradio_config = {"auth_required":true,"auth_message":null,"is_space":false,"root":""};</script>

    <link rel="preconnect" href="https://fonts.googleapis.com" />
    <link
        rel="preconnect"
        href="https://fonts.gstatic.com"
        crossorigin="anonymous"
    />
    <script src="https://cdnjs.cloudflare.com/ajax/libs/iframe-resizer/4.3.1/iframeResizer.contentWindow.min.js"></script>
    <script type="module" crossorigin src="./assets/index-ff81f4ae.js"></script>

</head>

<body
    style="
        width: 100%;
        margin: 0;
        padding: 0;
        display: flex;
        flex-direction: column;
        flex-grow: 1;
    "
>
    <h2 style="text-align: center;">Chat with AI Chatbot 🤖</h2>

    <form action="/ingest" enctype="multipart/form-data" method="post">
        <input name="files" type="file" multiple>
        <input type="submit">
    </form>

    <script>
        const ce = document.getElementsByTagName("gradio-app");
        if (ce[0]) {
        ce[0].addEventListener("domchange", () => {
            document.body.style.padding = "0";
        });
        document.body.style.padding = "0";
    }
    </script>
</body>
"""
    return HTMLResponse(content=content)


@db_router.post("/ingest")
async def create_ingest(file: UploadFile = File(...)):
    try:
        logger.info(f"File {file}")
        dest_path = f"samples/{file.filename}"
        logger.info(f"dest_path {dest_path}")
        with dest_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    finally:
        file.file.close()
