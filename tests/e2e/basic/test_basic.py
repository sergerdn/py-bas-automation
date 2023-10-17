import asyncio
import os

import pytest
from pywinauto import Application  # type: ignore

from pybas_automation.browser_automator import BrowserAutomator
from pybas_automation.browser_profile import BrowserProfileStorage
from pybas_automation.task import TaskStorage, TaskStorageModeEnum
from tests import is_windows


@pytest.mark.skipif(not is_windows, reason="requires Windows")
class TestBasic2e2:
    @pytest.mark.asyncio
    async def test_blah(self, bas_app: Application) -> None:
        print("test_blah")

    @pytest.mark.asyncio
    async def test_blah_another(self, bas_app: Application) -> None:
        print("test_blah_another")

    @pytest.mark.asyncio
    async def test_basic_compiled_app_works(self, bas_app: Application, fingerprint_key: str) -> None:
        """Test to check if the compiled app works as expected."""

        # Start the application by simulating a click on 'OK Enter' button
        bas_app.window(title="OK Enter", top_level_only=False).wrapper_object().click()

        # Give the app some time to process after the click
        await asyncio.sleep(5)

        # Wait for a new window to appear indicating the app has finished its operation
        while len(bas_app.windows()) != 2:
            print("Waiting for the app to finished...")
            await asyncio.sleep(5)

        # Print the local application data directory for debugging purposes
        print(os.environ["LOCALAPPDATA"])

        # Load tasks from the storage
        task_storage = TaskStorage(mode=TaskStorageModeEnum.READ_WRITE)
        assert task_storage.load_all() is True
        tasks = task_storage.get_all()
        assert tasks is not None
        assert len(tasks) == 1

        # Load browser profiles using the provided fingerprint key
        browser_profile_storage = BrowserProfileStorage(fingerprint_key=fingerprint_key)
        assert browser_profile_storage.count() == 1
        profiles = browser_profile_storage.load_all()
        profile = profiles[0]

        # Validate that the profile directory exists
        assert os.path.exists(profile.profile_dir)

        # Validate that our specific directory and fingerprint file exist within the profile directory
        assert os.path.exists(os.path.join(profile.profile_dir, ".pybas")) is True
        assert os.path.exists(os.path.join(profile.profile_dir, ".pybas", "fingerprint_raw.json")) is True

        # Ensure that the browser started by checking for the 'Default' directory within the profile directory
        assert os.path.exists(os.path.join(profile.profile_dir, "Default")) is True

    @pytest.mark.asyncio
    async def test_basic(self, bas_app: Application) -> None:
        pass

        # Finding the window which contains the radio buttons
        # Find the main window or parent which contains the DEBUG Static control
        debug_window = bas_app.window(title="DEBUG", control_type="Text", top_level_only=False)

        # Search for the "true" RadioButton among all descendants of the main window
        true_radiobutton = debug_window.parent().descendants(title="true", control_type="RadioButton")[0]

        # Interact with the found RadioButton
        true_radiobutton.click()

        # Start the application by simulating a click on 'OK Enter' button
        bas_app.window(title="OK Enter", top_level_only=False).wrapper_object().click()

        # Give the app some time to process after the click
        await asyncio.sleep(5)

        # Continuously check if the browser is clickable by evaluating the number of children of the browser's parent
        # window. In DEBUG mode, once the script finishes execution, the count of children should change,
        # signaling that the browser is clickable.
        browser_1_panel = bas_app.window(title="Show browser", control_type="Text", top_level_only=False)
        while len(browser_1_panel.wrapper_object().parent().children()) == 3:
            # Pause for 1 second before rechecking to prevent excessive CPU usage.
            await asyncio.sleep(1)

        # Print the local application data directory for debugging purposes
        print(os.environ["LOCALAPPDATA"])

        # Load tasks from the storage
        task_storage = TaskStorage(mode=TaskStorageModeEnum.READ)
        assert task_storage.load_all() is True
        tasks = task_storage.get_all()
        assert tasks is not None
        assert len(tasks) == 1

        task = tasks[0]
        task_id, unique_process_id, remote_debugging_port = (
            task.task_id,
            task.unique_process_id,
            task.remote_debugging_port,
        )
        assert task_id is not None
        assert unique_process_id is not None
        assert remote_debugging_port is not None

        print(task_id, unique_process_id, remote_debugging_port)

        async with BrowserAutomator(
            remote_debugging_port=remote_debugging_port, unique_process_id=unique_process_id
        ) as automator:
            ws_endpoint = automator.get_ws_endpoint()

            assert ws_endpoint is not None
            assert ws_endpoint.startswith("ws://")

            assert automator.browser_version is not None
            assert automator.browser_version.startswith("Chrome/")
            print(automator.browser_version)

            await automator.page.goto("https://playwright.dev/python/")
            elem = automator.page.locator("xpath=//a[@class='getStarted_Sjon']")
            await automator.bas_move_mouse_to_elem(elem=elem)
            await elem.click()

            page_content = await automator.bas_get_page_content()

            assert page_content is not None
            assert "html" in page_content
