import os
import shutil
import tempfile
from typing import Generator

import pytest
from _pytest.monkeypatch import MonkeyPatch


class BrowserProfileBase:
    @pytest.fixture(autouse=True)
    def run_around_tests(self) -> Generator[None, None, None]:
        monkeypatch = MonkeyPatch()
        test_dir = tempfile.mkdtemp(prefix="pybas-profile-storage-test_")

        assert os.path.exists(test_dir)
        assert os.path.isdir(test_dir)

        monkeypatch.setenv("LOCALAPPDATA", test_dir)
        try:
            yield
        finally:
            monkeypatch.undo()
            if os.path.exists(test_dir):
                shutil.rmtree(test_dir)
