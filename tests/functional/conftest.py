import os
import shutil
import tempfile
from typing import Callable, Dict, Generator, Union
from urllib.parse import parse_qs, urlencode, urlparse
from zipfile import ZipFile

import nest_asyncio  # type: ignore
import pytest
from _pytest.monkeypatch import MonkeyPatch
from playwright.sync_api import BrowserContext, sync_playwright
from pydantic import DirectoryPath

from tests import FIXTURES_DIR, _find_free_port

# Allow nested asyncio loops, https://stackoverflow.com/a/72453292
nest_asyncio.apply()


@pytest.fixture(scope="function", autouse=True)
def _mock_app_data_dir() -> Generator[None, None, None]:
    """
    Mocks the app data directory for the duration of the tests.
    """

    monkeypatch = MonkeyPatch()
    test_dir = tempfile.mkdtemp(prefix="pybas-mocks_test_")

    assert os.path.exists(test_dir)
    assert os.path.isdir(test_dir)

    monkeypatch.setenv("LOCALAPPDATA", test_dir)
    try:
        yield  # run tests
    finally:
        monkeypatch.undo()
        if os.path.exists(test_dir):
            shutil.rmtree(test_dir)


@pytest.fixture(scope="module")
def fingerprint_key() -> Union[str, None]:
    fingerprint_key = os.environ.get("FINGERPRINT_KEY", None)
    if not fingerprint_key:
        raise ValueError("FINGERPRINT_KEY not set")

    return fingerprint_key


@pytest.fixture(scope="module")
def fingerprint_str() -> str:
    fingerprint_str_zip = os.path.join(FIXTURES_DIR, "fingerprint_raw.zip")
    assert os.path.exists(fingerprint_str_zip)

    with ZipFile(fingerprint_str_zip) as zf:
        for file in zf.namelist():
            if not file == "fingerprint_raw.json":
                continue

            with zf.open(file) as f:
                return f.read().decode("utf-8")

    raise Exception("fingerprint_raw.json not found in fingerprint_raw.zip")


@pytest.fixture(scope="session")
def vcr_config() -> Dict[str, Callable]:
    def before_record_response(response):  # type: ignore
        if response["status_code"] != 200:
            return
        return response

    def before_record_request(request):  # type: ignore
        url = request.uri
        parsed = urlparse(url)

        # If the request is to localhost, do not record it
        if parsed.hostname == "localhost" or parsed.hostname == "127.0.0.1":
            return None

        parsed_qs = parse_qs(parsed.query)
        if parsed_qs.get("key", None):
            parsed_qs["key"] = ["dummy_key"]
            qs = urlencode(parsed_qs, doseq=True)
            url = parsed._replace(query=qs).geturl()

        request.uri = url

        return request

    return {"before_record_response": before_record_response, "before_record_request": before_record_request}


@pytest.fixture(scope="session")
def browser_profile_folder_path() -> Generator[DirectoryPath, None, None]:
    dir_name = DirectoryPath(tempfile.mkdtemp(dir=tempfile.gettempdir()))
    if not os.path.exists(dir_name):
        os.mkdir(dir_name)

    yield DirectoryPath(dir_name)

    shutil.rmtree(dir_name, ignore_errors=True)


@pytest.fixture(scope="session")
def free_port() -> int:
    return _find_free_port()


@pytest.fixture(scope="session")
def browser_data() -> Generator[tuple[BrowserContext, DirectoryPath, int], None, None]:
    user_data_dir = DirectoryPath(tempfile.mkdtemp(dir=tempfile.gettempdir()))
    port = _find_free_port()

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch_persistent_context(
            user_data_dir=user_data_dir,
            headless=True,
            # viewport={"width": 1366, "height": 4768},
            args=[f"--remote-debugging-port={port}"],
        )

        yield browser, user_data_dir, port

    shutil.rmtree(user_data_dir, ignore_errors=True)


@pytest.fixture(scope="module")
def brightdata_credentials() -> Dict[str, str]:
    username = os.environ.get("BRIGHTDATA_USERNAME", None)
    password = os.environ.get("BRIGHTDATA_PASSWORD", None)
    if username is None or password is None:
        raise ValueError("BRIGHTDATA_USERNAME or BRIGHTDATA_PASSWORD not set")

    return {"username": username, "password": password}
