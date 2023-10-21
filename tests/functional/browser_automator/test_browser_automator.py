import time

import pytest
from playwright.async_api import BrowserContext
from pydantic import DirectoryPath

from pybas_automation.browser_automator import BrowserAutomator, StorageStateModel
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

    @pytest.mark.asyncio
    async def test_save_load_browser_data(self, browser_data: tuple[BrowserContext, DirectoryPath, int]) -> None:
        """
        Test the BrowserAutomator's ability to communicate with a browser instance
        and verify the saving of browser data including cookies and local storage values.
        """

        # Unpack data related to the browser instance
        _, profile_folder_path, remote_debugging_port = browser_data
        browser_profile = BrowserProfile(profile_dir=profile_folder_path)

        # Establish communication with the browser using BrowserAutomator
        async with BrowserAutomator(
            browser_profile=browser_profile, remote_debugging_port=remote_debugging_port
        ) as automator:
            # Loop through each URL and its associated domain
            for url, domain in [
                ("https://playwright.dev/python/", "playwright.dev"),
                ("https://lumtest.com/echo.json", "lumtest.com"),
            ]:
                # Navigate to the specified URL and wait until network is idle
                await automator.page.goto(url=url, wait_until="networkidle")

                # Set a value in the local storage of the current domain
                await automator.page.evaluate(f"localStorage.setItem('key_{domain}', 'value_{domain}');")

                # Add a cookie specific to the current domain
                await automator.page.context.add_cookies(
                    [
                        {
                            "name": "cookie_name",
                            "value": "cookie_value",
                            "domain": domain,
                            "path": "/",
                            "expires": int(time.time()) + 3600,  # Set the cookie to expire in 1 hour
                        }
                    ]
                )

            # Save browser data (cookies, local storage, etc.) and verify the contents
            storage_state: StorageStateModel = await automator.export_browser_data()

            # Ensure cookies have been saved and retrieved correctly
            assert storage_state.cookies is not None
            assert len(storage_state.cookies) > 0

            # Ensure local storage values have been saved and retrieved correctly
            assert storage_state.origins is not None
            assert len(storage_state.origins) == 2

            # Clear all browser data and verify that the browser data has been cleared
            await automator.clear_browser_data()
            storage_state_clear: StorageStateModel = await automator.export_browser_data(save_to_file=False)
            assert len(storage_state_clear.cookies) == 0
            assert len(storage_state_clear.origins) == 0

            # Validate that the browser data have successfully been restored
            storage_state_imported: StorageStateModel = await automator.import_browser_data()
            assert len(storage_state_imported.cookies) == 2

            # TODO: because local storage values are not restored yet
            assert len(storage_state_imported.origins) == 0
