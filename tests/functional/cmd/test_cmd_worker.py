import codecs
import json
import os
from typing import Generator

import pytest
from click.testing import CliRunner
from playwright.async_api import BrowserContext
from pydantic import DirectoryPath

import cmd_initial
import cmd_worker


def create_tasks(runner: CliRunner, fingerprint_key: str) -> str:
    result = runner.invoke(cmd_initial.main, ["--bas_fingerprint_key", f"{fingerprint_key}", "--limit_tasks", "1"])

    assert result.exit_code == 0
    assert result.exception is None

    result_json = json.loads(result.output.strip())
    tasks_file = result_json.get("tasks_file", None)

    assert tasks_file is not None
    assert os.path.exists(tasks_file) is True

    return str(tasks_file)


@pytest.mark.vcr()
class TestCmdWorker:
    @pytest.fixture()
    def runner(self) -> Generator[CliRunner, None, None]:
        yield CliRunner()

    def test_main(
        self, runner: CliRunner, fingerprint_key: str, browser_data: tuple[BrowserContext, DirectoryPath, int]
    ) -> None:
        _, _, remote_debugging_port = browser_data

        task_file = create_tasks(runner, fingerprint_key)
        assert os.path.exists(task_file) is True

        tasks_json = json.loads(codecs.open(task_file, "r", "utf-8").read())

        task_id = tasks_json[0].get("task_id")
        assert task_id is not None

        result = runner.invoke(
            cmd_worker.main, ["--remote_debugging_port", f"{remote_debugging_port}", "--task_id", task_id]
        )

        assert result.exception is None
        assert result.exit_code == 0
