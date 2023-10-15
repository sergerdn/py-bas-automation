import codecs
import os
from typing import Union

import pytest

from tests import ABS_PATH, FIXTURES_DIR


@pytest.fixture(scope="module")
def xml_config() -> str:
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

    xml_config = xml_config.replace("{{PYTHON_RUN_COMMANDS}}", "poetry run python")

    xml_config = xml_config.replace("{{FINGERPRINT_KEY}}", fingerprint_key)
    xml_config = xml_config.replace("{{CMD_INITIAL}}", cmd_initial_filename)
    xml_config = xml_config.replace("{{CMD_WORKER}}", cmd_worker_filename)

    xml_config = xml_config.replace("{{BRIGHTDATA_USERNAME}}", proxy_username)
    xml_config = xml_config.replace("{{BRIGHTDATA_PASSWORD}}", proxy_password)

    # make sure we set all the required values
    assert "{{" not in xml_config
    assert "}}" not in xml_config

    return xml_config


@pytest.fixture(scope="module")
def task_id() -> Union[str, None]:
    task_id = os.environ.get("TEST_TASK_ID", None)
    if not task_id:
        raise ValueError("TEST_TASK_ID not set")

    return task_id


@pytest.fixture(scope="module")
def unique_process_id() -> Union[str, None]:
    unique_process_id = os.environ.get("TEST_UNIQUE_PROCESS_ID", None)
    if not unique_process_id:
        raise ValueError("TEST_UNIQUE_PROCESS_ID not set")

    return unique_process_id


@pytest.fixture(scope="module")
def remote_debugging_port() -> Union[int, None]:
    remote_debugging_port = os.environ.get("TEST_REMOTE_DEBUGGING_PORT", 0)
    if not remote_debugging_port:
        raise ValueError("TEST_REMOTE_DEBUGGING_PORT not set")

    return int(remote_debugging_port)
