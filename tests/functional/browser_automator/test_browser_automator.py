import pytest
from playwright.async_api import BrowserContext
from pydantic import DirectoryPath

from pybas_automation.browser_automator import BrowserAutomator
from pybas_automation.browser_automator.browser_automator import BrowserWsConnectError
from pybas_automation.browser_profile import BrowserProfile


class TestBrowserAutomator:
    @pytest.mark.asyncio
    async def test_expected_failed(self, free_port: int) -> None:
        """
        Test the scenario where connecting to the browser fails.
        This should raise a BrowserWsConnectError.
        """
        remote_debugging_port = free_port
        browser_profile = BrowserProfile()

        # Expect an error when trying to connect to the browser without a proper WebSocket debugging endpoint.
        with pytest.raises(BrowserWsConnectError):
            async with BrowserAutomator(
                browser_profile=browser_profile, remote_debugging_port=remote_debugging_port
            ) as automator:
                automator.connect()

    @pytest.mark.asyncio
    async def test_basic(self, browser_data: tuple[BrowserContext, DirectoryPath, int]) -> None:
        """
        Test the BrowserAutomator's ability to communicate with a browser instance.
        """
        # Unpack browser data
        browser, profile_folder_path, remote_debugging_port = browser_data
        browser_profile = BrowserProfile(profile_dir=profile_folder_path)

        # Create an instance of BrowserAutomator and communicate with the browser.
        async with BrowserAutomator(
            browser_profile=browser_profile, remote_debugging_port=remote_debugging_port
        ) as automator:
            # Send a command to the browser and ensure a valid response.
            data = await automator.cdp_client.send_command("Browser.getVersion")
            assert data is not None
            assert data.get("product", None) is not None

            # Ensure that the browser product version contains "Chrome/"
            assert "Chrome/" in data["product"]

            # Use the automator to navigate to a specific webpage.
            await automator.page.goto("https://lumtest.com/echo.json")
