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
    """Create tasks using the cmd_initial module and return the path to the tasks file."""

    # Invoke the main function of cmd_initial to create tasks
    result = runner.invoke(cmd_initial.main, ["--bas_fingerprint_key", f"{fingerprint_key}", "--limit_tasks", "1"])

    # Ensure the command executed successfully
    assert result.exit_code == 0
    assert result.exception is None

    # Parse the output as JSON and retrieve the tasks file path
    result_json = json.loads(result.output.strip())
    tasks_file = result_json.get("tasks_file", None)

    # Verify the tasks file exists
    assert tasks_file is not None
    assert os.path.exists(tasks_file) is True

    return str(tasks_file)


@pytest.mark.vcr()
class TestCmdWorker:
    @pytest.fixture()
    def runner(self) -> Generator[CliRunner, None, None]:
        """Fixture to provide a CliRunner instance for invoking command-line applications."""
        yield CliRunner()

    def test_main(
        self, runner: CliRunner, fingerprint_key: str, browser_data: tuple[BrowserContext, DirectoryPath, int]
    ) -> None:
        """Test the main function of cmd_worker module."""

        # Extract the remote debugging port from the browser data tuple
        _, _, remote_debugging_port = browser_data

        # Create tasks and get the path to the tasks file
        task_file = create_tasks(runner, fingerprint_key)
        assert os.path.exists(task_file) is True

        # Load the tasks from the file and retrieve the task ID
        tasks_json = json.loads(codecs.open(task_file, "r", "utf-8").read())
        task_id = tasks_json[0].get("task_id")
        assert task_id is not None

        # Invoke the main function of cmd_worker with the specified task ID and remote debugging port
        result = runner.invoke(
            cmd_worker.main, ["--remote_debugging_port", f"{remote_debugging_port}", "--task_id", task_id]
        )

        # Ensure the command executed successfully
        assert result.exception is None
        assert result.exit_code == 0
