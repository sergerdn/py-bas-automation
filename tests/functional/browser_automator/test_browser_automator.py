import pytest
from playwright.async_api import BrowserContext
from pydantic import DirectoryPath

from pybas_automation.browser_automator import BrowserAutomator
from pybas_automation.browser_automator.browser_automator import BrowserWsConnectError


class TestBrowserAutomator:
    @pytest.mark.asyncio
    async def test_expected_failed(self, free_port: int) -> None:
        remote_debugging_port = free_port

        with pytest.raises(BrowserWsConnectError):
            async with BrowserAutomator(remote_debugging_port=remote_debugging_port) as automator:
                automator.connect()

    @pytest.mark.asyncio
    async def test_browser_automator(self, browser_data: tuple[BrowserContext, DirectoryPath, int]) -> None:
        browser, profile_folder_path, remote_debugging_port = browser_data

        async with BrowserAutomator(remote_debugging_port=remote_debugging_port) as automator:
            data = await automator.cdp_client.send_command("Browser.getVersion")
            assert data is not None
            assert data.get("result", None) is not None
            assert data["result"].get("product", None) is not None
            assert "Chrome/" in data["result"]["product"]

            await automator.page.goto("https://lumtest.com/echo.json")
