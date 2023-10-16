import os
import shutil
import tempfile
from typing import Callable, Dict, Generator
from urllib.parse import parse_qs, urlencode, urlparse
from zipfile import ZipFile

import nest_asyncio  # type: ignore
import pytest
from playwright.sync_api import BrowserContext, sync_playwright
from pydantic import DirectoryPath

from tests import FIXTURES_DIR, _find_free_port

# Patch asyncio to support nested asynchronous event loops.
nest_asyncio.apply()


@pytest.fixture(scope="module")
def fingerprint_str() -> str:
    """
    Retrieve fingerprint data from a zipped fixture.

    :return: Contents of fingerprint_raw.json from fingerprint_raw.zip.
    """

    fingerprint_zip_path = os.path.join(FIXTURES_DIR, "fingerprint_raw.zip")
    assert os.path.exists(fingerprint_zip_path)

    with ZipFile(fingerprint_zip_path) as zf:
        for file in zf.namelist():
            if file == "fingerprint_raw.json":
                with zf.open(file) as f:
                    return f.read().decode("utf-8")

    raise FileNotFoundError("fingerprint_raw.json not found in the zip file.")


@pytest.fixture(scope="session")
def vcr_config() -> Dict[str, Callable]:
    """
    Configure VCR to selectively record and replay HTTP requests for tests.

    :return: VCR configuration dictionary.
    """

    def before_record_response(response):  # type: ignore
        return response if response["status_code"] == 200 else None

    def before_record_request(request):  # type: ignore
        if urlparse(request.uri).hostname in ["localhost", "127.0.0.1"]:
            return None  # Skip localhost requests

        # Mask sensitive query params (like API keys) for recording.
        parsed = urlparse(request.uri)
        parsed_qs = parse_qs(parsed.query)
        if "key" in parsed_qs:
            parsed_qs["key"] = ["dummy_key"]
            request.uri = parsed._replace(query=urlencode(parsed_qs, doseq=True)).geturl()

        return request

    return {"before_record_response": before_record_response, "before_record_request": before_record_request}


@pytest.fixture(scope="session")
def browser_profile_folder_path() -> Generator[DirectoryPath, None, None]:
    """
    Provide a temporary directory for the browser profile.

    :return: Path to the temporary directory.
    """

    temp_dir = DirectoryPath(tempfile.mkdtemp())
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture(scope="session")
def free_port() -> int:
    """
    Fetch an available port on the host machine.

    :return: Free port number.
    """

    return _find_free_port()


@pytest.fixture(scope="session")
def browser_data() -> Generator[tuple[BrowserContext, DirectoryPath, int], None, None]:
    """
    Initialize a browser with a given user data directory and remote debugging port.

    :return: Tuple containing the BrowserContext, user data directory path, and remote debugging port.
    """

    user_data_dir = DirectoryPath(tempfile.mkdtemp())
    port = _find_free_port()

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch_persistent_context(
            user_data_dir=user_data_dir,
            headless=True,
            args=[f"--remote-debugging-port={port}"],
        )

        yield browser, user_data_dir, port

    shutil.rmtree(user_data_dir, ignore_errors=True)


@pytest.fixture(scope="module")
def brightdata_credentials() -> Dict[str, str]:
    """
    Fetch Bright Data service credentials from environment variables.

    :return: Dictionary containing username and password.
    """

    username = os.environ.get("BRIGHTDATA_USERNAME")
    password = os.environ.get("BRIGHTDATA_PASSWORD")
    if not username or not password:
        raise ValueError("Both BRIGHTDATA_USERNAME and BRIGHTDATA_PASSWORD must be set.")

    return {"username": username, "password": password}
