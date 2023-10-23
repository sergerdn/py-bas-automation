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

    import pytest

    @pytest.mark.asyncio
    async def test_local_storage_with_cdp_and_js(self, browser_data: tuple[BrowserContext, DirectoryPath, int]) -> None:
        """
        This test verifies the correct functionality of local storage interactions within a browser context using the
        BrowserAutomator. It navigates to specified URLs, performs local storage operations, and validates that these
        operations succeed. The test covers setting, retrieving, and clearing local storage items,
        as well as interacting with local storage through the Chrome DevTools Protocol.
        """

        # Extract the browser context, profile directory path, and remote debugging port from the provided tuple.
        _, profile_folder_path, remote_debugging_port = browser_data

        # Initialize the browser profile with the specified directory path.
        browser_profile = BrowserProfile(profile_dir=profile_folder_path)

        # Use the BrowserAutomator to establish a communication channel with the browser.
        async with BrowserAutomator(
            browser_profile=browser_profile, remote_debugging_port=remote_debugging_port
        ) as automator:
            # Define a list of tuples containing URLs to visit and their associated domains.
            url_domain_pairs = [
                ("https://playwright.dev/python/", "playwright.dev"),
                ("https://lumtest.com/echo.json", "lumtest.com"),
            ]

            # Iterate through each URL and its associated domain.
            for url, domain in url_domain_pairs:
                # Navigate to the URL and wait until network activity is idle to ensure all resources are loaded.
                await automator.page.goto(url=url, wait_until="networkidle")

                # Wait for the page to reach a 'loaded' state to ensure all DOM content is fully parsed.
                await automator.page.wait_for_load_state("domcontentloaded")

                # Retrieve the security origin of the current frame for later use in Chrome DevTools Protocol commands.
                security_origin = await automator.page.evaluate("window.location.origin")
                assert security_origin is not None, "Failed to retrieve the security origin."

                # Set a local storage item and verify its presence and value.
                await automator.page.evaluate(f"localStorage.setItem('key_{domain}', 'value_{domain}');")
                item = await automator.page.evaluate(f"localStorage.getItem('key_{domain}');")
                assert (
                    item == f"value_{domain}"
                ), f"Expected local storage item 'key_{domain}' to have value 'value_{domain}'."

                # Clear all local storage items and verify the specified item is no longer present.
                await automator.page.evaluate("localStorage.clear();")
                item = await automator.page.evaluate(f"localStorage.getItem('key_{domain}');")
                assert item is None, "Expected local storage to be empty after clearing."

                # Set a local storage item using Chrome DevTools Protocol and verify its presence and value.
                await automator.cdp_session.send(
                    "DOMStorage.setDOMStorageItem",
                    {
                        "storageId": {
                            "securityOrigin": security_origin,
                            "isLocalStorage": True,
                        },
                        "key": f"new_key_{domain}",
                        "value": f"new_value_{domain}",
                    },
                )
                item = await automator.page.evaluate(f"localStorage.getItem('new_key_{domain}');")
                assert (
                    item == f"new_value_{domain}"
                ), f"Expected local storage item 'new_key_{domain}' to have value 'new_value_{domain}'."
