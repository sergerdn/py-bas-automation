import asyncio
import codecs
import os
import tempfile
import zipfile
from typing import AsyncGenerator

import pytest_asyncio
from pywinauto import Application  # type: ignore

from tests import ABS_PATH, FIXTURES_DIR
from tests.e2e import clean_dir


def generate_xml_config() -> str:
    """
    Prepares the XML config for the e2e tests.
    """
    fingerprint_key = os.environ.get("FINGERPRINT_KEY", None)
    assert fingerprint_key is not None
    assert len(fingerprint_key) == 64

    xml_config_path = os.path.join(FIXTURES_DIR, "Actual.PyBasFree.xml.default.xml")
    assert os.path.exists(xml_config_path)
    assert os.path.isfile(xml_config_path)

    cmd_initial_filename = os.path.join(ABS_PATH, "cmd_initial.py")
    assert os.path.exists(cmd_initial_filename)
    assert os.path.isfile(cmd_initial_filename)
    cmd_worker_filename = os.path.join(ABS_PATH, "cmd_worker.py")
    assert os.path.exists(cmd_worker_filename)
    assert os.path.isfile(cmd_worker_filename)

    proxy_username = os.environ.get("BRIGHTDATA_USERNAME", None)
    proxy_password = os.environ.get("BRIGHTDATA_PASSWORD", None)
    if proxy_username is None or proxy_password is None:
        raise ValueError("BRIGHTDATA_USERNAME or BRIGHTDATA_PASSWORD not set")

    with codecs.open(xml_config_path, "r", "utf-8") as f:
        xml_config = f.read()

    assert "{{PYTHON_RUN_COMMANDS}}" in xml_config
    xml_config = xml_config.replace("{{PYTHON_RUN_COMMANDS}}", "poetry run python")

    assert "{{FINGERPRINT_KEY}}" in xml_config
    xml_config = xml_config.replace("{{FINGERPRINT_KEY}}", fingerprint_key)

    assert "{{CMD_INITIAL}}" in xml_config
    xml_config = xml_config.replace("{{CMD_INITIAL}}", cmd_initial_filename)
    assert "{{CMD_WORKER}}" in xml_config
    xml_config = xml_config.replace("{{CMD_WORKER}}", cmd_worker_filename)

    assert "{{BRIGHTDATA_USERNAME}}" in xml_config
    xml_config = xml_config.replace("{{BRIGHTDATA_USERNAME}}", proxy_username)
    assert "{{BRIGHTDATA_PASSWORD}}" in xml_config
    xml_config = xml_config.replace("{{BRIGHTDATA_PASSWORD}}", proxy_password)

    assert "{{LIMIT_TASKS}}" in xml_config
    xml_config = xml_config.replace("{{LIMIT_TASKS}}", "1")
    assert "{{THREADS}}" in xml_config
    xml_config = xml_config.replace("{{THREADS}}", "1")

    # make sure we set all the required values
    assert "{{" not in xml_config
    assert "}}" not in xml_config

    return xml_config


@pytest_asyncio.fixture(scope="function")
async def bas_app() -> AsyncGenerator[Application, None]:
    xml_config = generate_xml_config()

    src = os.path.join(ABS_PATH, "bas_release", "PyBasFree.zip")
    assert os.path.exists(src)
    assert os.path.isfile(src)
    test_dir = tempfile.mkdtemp(prefix="pybas-e2e_test_")
    assert os.path.exists(test_dir)

    try:
        with zipfile.ZipFile(src, "r") as zip_ref:
            zip_ref.extractall(test_dir)

        unpacked_dir = os.path.join(test_dir, "PyBasFree")
        assert os.path.exists(unpacked_dir)
        assert os.path.isdir(unpacked_dir)

        print(unpacked_dir)
        exe_filename = os.path.join(unpacked_dir, "PyBasFree.exe")

        app = Application(backend="uia").start(exe_filename)

        # wait for the app to download dependencies and detached from the console
        while app.is_process_running():
            await asyncio.sleep(5)

        app = Application(backend="uia").connect(title="Language chooser", timeout=10)
        await asyncio.sleep(5)
        assert app.is_process_running() is True

        btn_wrapper = app.window(title="OK Enter", top_level_only=False).wrapper_object()
        btn_wrapper.click()
        assert app.is_process_running() is True

        await asyncio.sleep(5)
        # closing the app
        app.kill()
        while app.is_process_running():
            await asyncio.sleep(5)

        created_dirs = os.listdir(os.path.join(unpacked_dir, "appsremote", "PyBasFree"))

        # Get the first directory starting with 'SID'
        matching_dir = next((x for x in created_dirs if x.startswith("SID")), None)
        assert matching_dir is not None

        xml_config_filename = os.path.join(
            unpacked_dir, "appsremote", "PyBasFree", matching_dir, "engine", "Actual.PyBasFree.xml"
        )

        with codecs.open(xml_config_filename, "w", "utf-8") as f:
            f.write(xml_config)

        app = Application(backend="uia").start(exe_filename)

        while app.is_process_running():
            await asyncio.sleep(5)

        app = Application(backend="uia").connect(title_re="^PyBasFree", timeout=10)
        assert app.is_process_running() is True

        try:
            yield app
        finally:
            app.kill()
            while app.is_process_running():
                await asyncio.sleep(1)
    finally:
        await clean_dir(test_dir)
