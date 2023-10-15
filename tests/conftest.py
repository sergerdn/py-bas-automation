import os
import shutil
import tempfile
from typing import Generator

import pytest
from _pytest.monkeypatch import MonkeyPatch


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
