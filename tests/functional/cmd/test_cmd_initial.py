import json
import os
from typing import Dict, Generator

import pytest
from click.testing import CliRunner

import cmd_initial


@pytest.mark.vcr()
class TestCmdInitial:
    @pytest.fixture()
    def runner(self) -> Generator[CliRunner, None, None]:
        """Fixture to provide a CliRunner instance for invoking command-line applications."""
        yield CliRunner()

    def test_main(self, runner: CliRunner, fingerprint_key: str) -> None:
        """Test the main function of cmd_initial with basic arguments."""

        # Invoke the main function with fingerprint key and a task limit
        result = runner.invoke(cmd_initial.main, ["--bas_fingerprint_key", f"{fingerprint_key}", "--limit_tasks", "1"])

        # Ensure the command executed successfully
        assert result.exit_code == 0
        assert result.exception is None

        # Parse the output as JSON and check if tasks_file is present
        result_json = json.loads(result.output.strip())
        tasks_file = result_json.get("tasks_file", None)
        assert tasks_file is not None

        # Ensure the tasks file was created on the filesystem
        assert os.path.exists(tasks_file) is True

    def test_main_proxy(self, runner: CliRunner, fingerprint_key: str, brightdata_credentials: Dict[str, str]) -> None:
        """Test the main function of cmd_initial with proxy arguments."""

        # Extract proxy credentials from the provided dictionary
        proxy_username, proxy_password = brightdata_credentials["username"], brightdata_credentials["password"]
        assert proxy_username is not None
        assert proxy_password is not None

        # Invoke the main function with fingerprint key, task limit and proxy arguments
        result = runner.invoke(
            cmd_initial.main,
            [
                "--bas_fingerprint_key",
                f"{fingerprint_key}",
                "--limit_tasks",
                "1",
                "--proxy_provider",
                "brightdata",
                "--proxy_username",
                proxy_username,
                "--proxy_password",
                proxy_password,
            ],
        )

        # Ensure the command executed successfully with proxy configuration
        assert result.exception is None
        assert result.exit_code == 0
