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

    # Fetch and validate the fingerprint key from environment variables
    fingerprint_key = os.environ.get("FINGERPRINT_KEY", None)
    assert fingerprint_key is not None
    assert len(fingerprint_key) == 64

    # Validate the presence of XML config and command files
    xml_config_path = os.path.join(FIXTURES_DIR, "Actual.PyBasFree.xml.default.xml")
    assert os.path.exists(xml_config_path)
    assert os.path.isfile(xml_config_path)

    cmd_initial_filename = os.path.join(ABS_PATH, "cmd_initial.py")
    assert os.path.exists(cmd_initial_filename)
    assert os.path.isfile(cmd_initial_filename)
    cmd_worker_filename = os.path.join(ABS_PATH, "cmd_worker.py")
    assert os.path.exists(cmd_worker_filename)
    assert os.path.isfile(cmd_worker_filename)

    # Fetch and validate the proxy credentials from environment variables
    proxy_username = os.environ.get("BRIGHTDATA_USERNAME", None)
    proxy_password = os.environ.get("BRIGHTDATA_PASSWORD", None)
    if proxy_username is None or proxy_password is None:
        raise ValueError("BRIGHTDATA_USERNAME or BRIGHTDATA_PASSWORD not set")

    # Read the xml config and replace placeholders with respective values
    with codecs.open(xml_config_path, "r", "utf-8") as f:
        xml_config = f.read()

    # Setting various configurations in the xml
    xml_config = xml_config.replace("{{PYTHON_RUN_COMMANDS}}", "poetry run python")
    xml_config = xml_config.replace("{{FINGERPRINT_KEY}}", fingerprint_key)
    xml_config = xml_config.replace("{{CMD_INITIAL}}", cmd_initial_filename)
    xml_config = xml_config.replace("{{CMD_WORKER}}", cmd_worker_filename)
    xml_config = xml_config.replace("{{BRIGHTDATA_USERNAME}}", proxy_username)
    xml_config = xml_config.replace("{{BRIGHTDATA_PASSWORD}}", proxy_password)
    xml_config = xml_config.replace("{{LIMIT_TASKS}}", "1")
    xml_config = xml_config.replace("{{THREADS}}", "1")

    # Ensure all placeholders are replaced
    assert "{{" not in xml_config
    assert "}}" not in xml_config

    return xml_config


@pytest_asyncio.fixture(scope="function")
async def bas_app() -> AsyncGenerator[Application, None]:
    """
    Asynchronous pytest fixture that sets up, runs, and tears down the application for e2e tests.
    """

    # Generate xml configuration required to run the application
    xml_config = generate_xml_config()

    # Define the path to the zipped application release
    src = os.path.join(ABS_PATH, "bas_release", "PyBasFree.zip")
    assert os.path.exists(src)
    assert os.path.isfile(src)

    # Create a temporary directory to extract and run the application
    test_dir = tempfile.mkdtemp(prefix="pybas-e2e_test_")
    assert os.path.exists(test_dir)

    try:
        # Extract the zipped application to the temporary directory
        with zipfile.ZipFile(src, "r") as zip_ref:
            zip_ref.extractall(test_dir)

        # Define the directory path where the application was extracted
        unpacked_dir = os.path.join(test_dir, "PyBasFree")
        assert os.path.exists(unpacked_dir)
        assert os.path.isdir(unpacked_dir)

        # Define the path to the executable of the application
        exe_filename = os.path.join(unpacked_dir, "PyBasFree.exe")

        # Start the application
        app = Application(backend="uia").start(exe_filename)

        # Periodically check the application until its initial setup (e.g., dependency download) is complete
        while app.is_process_running():
            await asyncio.sleep(5)

        # Reconnect to the application after its setup is complete
        app = Application(backend="uia").connect(title="Language chooser", timeout=10)
        await asyncio.sleep(5)
        assert app.is_process_running() is True

        # Simulate a user click on the 'OK Enter' button in the application
        btn_wrapper = app.window(title="OK Enter", top_level_only=False).wrapper_object()
        btn_wrapper.click()
        assert app.is_process_running() is True

        # Give the application some time to process after the click
        await asyncio.sleep(5)

        # Close the application
        app.kill()
        while app.is_process_running():
            await asyncio.sleep(5)

        # List directories under 'appsremote' to find the application's session directory
        created_dirs = os.listdir(os.path.join(unpacked_dir, "appsremote", "PyBasFree"))

        # Get the first directory starting with 'SID' which represents the application's session
        matching_dir = next((x for x in created_dirs if x.startswith("SID")), None)
        assert matching_dir is not None

        # Define the path to the XML configuration file of the application
        xml_config_filename = os.path.join(
            unpacked_dir, "appsremote", "PyBasFree", matching_dir, "engine", "Actual.PyBasFree.xml"
        )

        # Write the generated xml configuration to the appropriate location
        with codecs.open(xml_config_filename, "w", "utf-8") as f:
            f.write(xml_config)

        # Restart the application with the new configurations
        app = Application(backend="uia").start(exe_filename)

        # Periodically check the application until it's fully loaded
        while app.is_process_running():
            await asyncio.sleep(5)

        # Reconnect to the application main window
        app = Application(backend="uia").connect(title_re="^PyBasFree", timeout=10)
        assert app.is_process_running() is True

        try:
            # Yield the connected application instance for the tests to run
            yield app
        finally:
            # Close the application after the tests are done
            app.kill()
            while app.is_process_running():
                await asyncio.sleep(1)
    finally:
        # Clean up by deleting the temporary directory
        await clean_dir(test_dir)
