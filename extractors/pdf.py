import os
import logging
import tempfile
import requests
from abc import ABC
from typing import Iterator, List
from urllib.parse import urlparse
from pathlib import Path

from extractors import BaseLoader, Blob, BaseBlobParser
from databases import Document


logger = logging.getLogger(__file__)


class BasePDFLoader(BaseLoader, ABC):
    """Base loader class for PDF files.

    Defaults to check for local file, but if the file is a web path, it will download it
    to a temporary file, and use that, then clean up the temporary file after completion
    """

    def __init__(self, file_path: str):
        """Initialize with file path."""
        self.file_path = file_path
        self.web_path = None
        if "~" in self.file_path:
            self.file_path = os.path.expanduser(self.file_path)

        # If the file is a web path, download it to a temporary file, and use that
        if not os.path.isfile(self.file_path) and self._is_valid_url(self.file_path):
            r = requests.get(self.file_path)

            if r.status_code != 200:
                raise ValueError(
                    "Check the url of your file; returned status code %s"
                    % r.status_code
                )

            self.web_path = self.file_path
            self.temp_file = tempfile.NamedTemporaryFile()
            self.temp_file.write(r.content)
            self.file_path = self.temp_file.name
        elif not os.path.isfile(self.file_path):
            raise ValueError("File path %s is not a valid file or url" % self.file_path)

    def __del__(self) -> None:
        if hasattr(self, "temp_file"):
            self.temp_file.close()

    @staticmethod
    def _is_valid_url(url: str) -> bool:
        """Check if the url is valid."""
        parsed = urlparse(url)
        return bool(parsed.netloc) and bool(parsed.scheme)

    @property
    def source(self) -> str:
        return self.web_path if self.web_path is not None else self.file_path


class PyPDFParser(BaseBlobParser):
    """Loads a PDF with pypdf and chunks at character level."""

    def lazy_parse(self, blob: Blob) -> Iterator[Document]:
        """Lazily parse the blob."""
        import pypdf

        with blob.as_bytes_io() as pdf_file_obj:
            pdf_reader = pypdf.PdfReader(pdf_file_obj)
            yield from [
                Document(
                    content=page.extract_text(),
                    metadata={"source": blob.source, "page": page_number+1},
                )
                for page_number, page in enumerate(pdf_reader.pages)
            ]


class PyPDFLoader(BasePDFLoader):
    """Loads a PDF with pypdf and chunks at character level.

    Loader also stores page numbers in metadatas.
    """

    def __init__(self, file_path: str) -> None:
        """Initialize with file path."""
        try:
            import pypdf  # noqa:F401
        except ImportError:
            raise ImportError(
                "pypdf package not found, please install it with " "`poetry add pypdf`"
            )
        self.parser = PyPDFParser()
        super().__init__(file_path)

    def load(self) -> List[Document]:
        """Load given path as pages."""
        return list(self.lazy_load())

    def lazy_load(
        self,
    ) -> Iterator[Document]:
        """Lazy load given path as pages."""
        blob = Blob.from_path(self.file_path)
        yield from self.parser.parse(blob)


class PyPDFDirectoryLoader(BaseLoader):
    """Loads a directory with PDF files with pypdf and chunks at character level.

    Loader also stores page numbers in metadatas.
    """

    def __init__(
        self,
        path: str,
        glob: str = "**/[!.]*.pdf",
        silent_errors: bool = False,
        load_hidden: bool = False,
        recursive: bool = False,
    ):
        self.path = path
        self.glob = glob
        self.load_hidden = load_hidden
        self.recursive = recursive
        self.silent_errors = silent_errors

    @staticmethod
    def _is_visible(path: Path) -> bool:
        return not any(part.startswith(".") for part in path.parts)

    def load(self) -> List[Document]:
        p = Path(self.path)
        docs = []
        items = p.rglob(self.glob) if self.recursive else p.glob(self.glob)
        for i in items:
            if i.is_file():
                if self._is_visible(i.relative_to(p)) or self.load_hidden:
                    try:
                        loader = PyPDFLoader(str(i))
                        sub_docs = loader.load()
                        for doc in sub_docs:
                            doc.metadata["source"] = str(i)
                        docs.extend(sub_docs)
                    except Exception as e:
                        if self.silent_errors:
                            logger.warning(e)
                        else:
                            raise e
        return docs
