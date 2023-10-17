import os
import shutil
import tempfile
import time
from typing import Generator, Union

import pytest
from _pytest.monkeypatch import MonkeyPatch


@pytest.fixture(scope="function", autouse=True)
def _mock_app_data_dir() -> Generator[None, None, None]:
    """
    Mocks the app data directory for the duration of the tests.
    This fixture is automatically applied to every test due to `autouse=True`.
    """

    # Get a MonkeyPatch object to override environment variables and other attributes.
    monkeypatch = MonkeyPatch()

    # Create a temporary directory to mock the app data directory.
    test_dir = tempfile.mkdtemp(prefix="pybas-mocks_test_")
    assert os.path.exists(test_dir)
    assert os.path.isdir(test_dir)

    # Override the "LOCALAPPDATA" environment variable to use the temporary directory.
    monkeypatch.setenv("LOCALAPPDATA", test_dir)

    try:
        yield  # run tests which use this fixture
    finally:
        # Once tests are done, undo the monkey patch and clean up the temporary directory.
        monkeypatch.undo()
        if os.path.exists(test_dir):
            for _x in range(0, 60):
                try:
                    shutil.rmtree(test_dir)
                except Exception:  # type: ignore
                    time.sleep(1)
                    continue
                break

            shutil.rmtree(test_dir, ignore_errors=True)


@pytest.fixture(scope="module")
def fingerprint_key() -> Union[str, None]:
    """
    Returns the fingerprint key from the environment variables.

    :return: Fingerprint key
    :raises ValueError: If the fingerprint key is not set
    """

    fingerprint_key = os.environ.get("FINGERPRINT_KEY", None)
    if not fingerprint_key:
        raise ValueError("FINGERPRINT_KEY not set")

    return fingerprint_key
