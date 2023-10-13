import httpx
import os
import posixpath
from fastapi import HTTPException


def strip_url(orig_url: str) -> str:
    """
    Strips the query parameters and trailing slash from a URL.
    """
    parsed_url = httpx.URL(orig_url)
    stripped_url = parsed_url.copy_with(query=None)
    stripped_url = str(stripped_url)
    return stripped_url.rstrip("/")


def safe_join(directory: str, path: str) -> str:
    """Safely path to a base directory to avoid escaping the base directory.
    Borrowed from: werkzeug.security.safe_join"""
    _os_alt_seps = [
        sep for sep in [os.path.sep, os.path.altsep] if sep is not None and sep != "/"
    ]

    if path == "":
        raise HTTPException(400)

    filename = posixpath.normpath(path)
    fullpath = os.path.join(directory, filename)
    if (
        any(sep in filename for sep in _os_alt_seps)
        or os.path.isabs(filename)
        or filename == ".."
        or filename.startswith("../")
        or os.path.isdir(fullpath)
    ):
        raise HTTPException(403)

    if not os.path.exists(fullpath):
        raise HTTPException(404, "File not found")

    return fullpath
