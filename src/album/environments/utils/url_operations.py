"""Module for handling operations with urls."""
from pathlib import Path
from typing import Union

import requests
from album.runner import album_logging
from requests.adapters import HTTPAdapter
from urllib3.util import Retry

from album.environments.utils.file_operations import create_path_recursively

module_logger = album_logging.get_active_logger


def is_downloadable(url: str) -> bool:
    """Show if url is a downloadable resource."""
    with _get_session() as s:
        h = s.head(url, allow_redirects=True)  # type: ignore
        header = h.headers
        content_type = header.get("content-type")  # type: ignore
        if "html" in content_type.lower():
            return False
        return True


def download_resource(url: str, path: Union[str, Path]) -> Path:
    """Download a resource given its url."""
    module_logger().debug(f"Download url {url} to {path}...")

    path = Path(path)  # type: ignore

    if not is_downloadable(url):
        raise AssertionError('Resource "%s" not downloadable!' % url)

    r = _request_get(url)

    create_path_recursively(path.parent)
    with open(path, "wb") as f:
        for chunk in r:
            f.write(chunk)

    return path


def _get_session() -> requests.Session:
    s = requests.Session()
    retry = Retry(connect=3, backoff_factor=0.5)

    adapter = HTTPAdapter(max_retries=retry)

    s.mount("http://", adapter)
    s.mount("https://", adapter)

    return s


def _request_get(url: str) -> requests.Response:
    """Get a response from a request to a resource url."""
    with _get_session() as s:
        r = s.get(url, allow_redirects=True, stream=True)  # type: ignore

        if r.status_code != 200:
            raise ConnectionError("Could not connect to resource %s!" % url)

        return r
