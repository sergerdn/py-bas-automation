import asyncio
import codecs
import os
import zipfile
from typing import AsyncGenerator, Generator

import pytest
import pytest_asyncio
from pydantic import FilePath
from pywinauto import Application  # type: ignore
from pywinauto.timings import TimeoutError  # type: ignore

from tests import ABS_PATH, FIXTURES_DIR
from tests.e2e import FILE_LOCK_FILENAME, FIXTURES_TEMP_DIR


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    loop = asyncio.get_event_loop()
    yield loop
    loop.close()


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


def write_xml_config() -> None:
    # Generate xml configuration required to run the application
    xml_config = generate_xml_config()

    # Define the directory path where the application was extracted
    working_dir = os.path.join(FIXTURES_TEMP_DIR, "PyBasFree")

    assert os.path.exists(working_dir)
    assert os.path.isdir(working_dir)

    # List directories under 'appsremote' to find the application's session directory
    created_dirs = os.listdir(os.path.join(working_dir, "appsremote", "PyBasFree"))

    # Get the first directory starting with 'SID' which represents the application's session
    matching_dir = next((x for x in created_dirs if x.startswith("SID")), None)
    assert matching_dir is not None

    # Define the path to the XML configuration file of the application
    xml_config_filename = os.path.join(
        working_dir, "appsremote", "PyBasFree", matching_dir, "engine", "Actual.PyBasFree.xml"
    )

    # Write the generated xml configuration to the appropriate location
    with codecs.open(xml_config_filename, "w", "utf-8") as f:
        f.write(xml_config)

    assert os.path.exists(xml_config_filename)


@pytest_asyncio.fixture(scope="session", autouse=True)
async def _prepared_fixtures_dir() -> AsyncGenerator[str, None]:
    if not os.path.exists(FIXTURES_TEMP_DIR):
        os.mkdir(FIXTURES_TEMP_DIR)
    print("Created temporary directory for e2e tests:", FIXTURES_TEMP_DIR)

    yield FIXTURES_TEMP_DIR

    print("All tests finished. Cleaning up...")
    # Clean up by deleting the temporary directory
    # await clean_dir(FIXTURES_TEMP_DIR)


async def start_app(exe_path: FilePath) -> Application:
    assert exe_path.exists() and exe_path.is_file()

    app = Application(backend="uia").start(str(exe_path))

    # Periodically check the application until its initial setup
    # (e.g., dependency download) is complete and detached from the process
    await ensure_process_not_running(app=app)

    return app


async def ensure_process_not_running(app: Application, timeout: int = 60) -> None:
    """
    Asynchronously ensures that the application process is not running.
    :param app: The application instance.
    :param timeout: The timeout in seconds.

    :raises ValueError: If the application process is still running after the timeout.
    """

    for _ in range(0, timeout):
        if app.is_process_running():
            await asyncio.sleep(1)
            continue
        break

    if app.is_process_running():
        raise ValueError("Application process is still running")


@pytest_asyncio.fixture(scope="session", autouse=True)
async def _prepare_bas_app(_prepared_fixtures_dir: str) -> str:
    """
    Asynchronous pytest fixture that sets up, runs, and tears down the application for e2e tests.
    """

    with FILE_LOCK_FILENAME:
        # Define the path to the zipped application release
        src_zip_filename = os.path.join(ABS_PATH, "bas_release", "PyBasFree.zip")
        assert os.path.exists(src_zip_filename)
        assert os.path.isfile(src_zip_filename)

        # Create a temporary directory to extract and run the application
        assert os.path.exists(_prepared_fixtures_dir)

        # Extract the zipped application to the temporary directory
        with zipfile.ZipFile(src_zip_filename, "r") as zip_ref:
            zip_ref.extractall(_prepared_fixtures_dir)

        # Define the directory path where the application was extracted
        working_dir = os.path.join(_prepared_fixtures_dir, "PyBasFree")
        assert os.path.exists(working_dir)
        assert os.path.isdir(working_dir)

        # Define the path to the executable of the application
        exe_path = os.path.join(working_dir, "PyBasFree.exe")

        # Start the application
        await start_app(exe_path=FilePath(exe_path))

        # Reconnect to the application after its setup is complete
        try:
            app = Application(backend="uia").connect(title="Language chooser", timeout=10)
        except TimeoutError:
            # not first run
            pass
        else:
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
            await ensure_process_not_running(app=app)

            write_xml_config()

            # Restart the application with the new configurations
            await start_app(exe_path=FilePath(exe_path))

        # write fresh new config
        write_xml_config()

        # Reconnect to the application main window
        app = Application(backend="uia").connect(title_re="^PyBasFree", timeout=10)
        assert app.is_process_running() is True

        app.kill()
        await ensure_process_not_running(app=app)
        await asyncio.sleep(5)

        return exe_path


@pytest_asyncio.fixture(scope="function")
async def bas_app() -> AsyncGenerator[Application, None]:
    exe_path = os.path.join(FIXTURES_TEMP_DIR, "PyBasFree", "PyBasFree.exe")

    with FILE_LOCK_FILENAME:
        write_xml_config()

        # Restart the application with the new configurations
        app = await start_app(exe_path=FilePath(exe_path))
        await ensure_process_not_running(app=app)

        # Reconnect to the application main window
        app = Application(backend="uia").connect(title_re="^PyBasFree", timeout=10)
        assert app.is_process_running() is True

        try:
            # Yield the connected application instance for the tests to run
            yield app
        finally:
            # Close the application after the tests are done
            app.kill()
            await ensure_process_not_running(app=app)
