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
        yield CliRunner()

    def test_main(self, runner: CliRunner, fingerprint_key: str) -> None:
        result = runner.invoke(cmd_initial.main, ["--bas_fingerprint_key", f"{fingerprint_key}", "--limit_tasks", "1"])

        assert result.exit_code == 0
        assert result.exception is None

        result_json = json.loads(result.output.strip())
        tasks_file = result_json.get("tasks_file", None)
        assert tasks_file is not None

        assert os.path.exists(tasks_file) is True

    def test_main_proxy(self, runner: CliRunner, fingerprint_key: str, brightdata_credentials: Dict[str, str]) -> None:
        proxy_username, proxy_password = brightdata_credentials["username"], brightdata_credentials["password"]
        assert proxy_username is not None
        assert proxy_password is not None

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

        assert result.exception is None
        assert result.exit_code == 0
