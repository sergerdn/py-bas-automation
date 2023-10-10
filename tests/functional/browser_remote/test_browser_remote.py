import pytest
from playwright.sync_api import BrowserContext
from pydantic import DirectoryPath

from pybas_automation.browser_remote import BrowserRemote, BrowserRemoteDebuggingPortNotAvailableError


class TestBrowserRemote:
    def test_expected_failed(self, free_port: int) -> None:
        remote_debugging_port = free_port

        remote_browser = BrowserRemote(remote_debugging_port=remote_debugging_port)
        with pytest.raises(BrowserRemoteDebuggingPortNotAvailableError):
            remote_browser.find_ws()

    def test_find(self, browser_data: tuple[BrowserContext, DirectoryPath, int]) -> None:
        browser, profile_folder_path, remote_debugging_port = browser_data
        page = browser.pages[0]
        page.goto("https://lumtest.com/echo.json")

        remote_browser = BrowserRemote(remote_debugging_port=remote_debugging_port)
        assert remote_browser.find_ws() is True
