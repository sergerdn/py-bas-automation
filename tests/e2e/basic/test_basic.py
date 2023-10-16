import asyncio
import os
import platform

import pytest
from pywinauto import Application  # type: ignore

from pybas_automation.browser_profile import BrowserProfileStorage
from pybas_automation.task import TaskStorage, TaskStorageModeEnum


# def is_ready_for_e2e() -> bool:
#     task_id = os.environ.get("TEST_TASK_ID", None)
#     if not task_id:
#         return False
#
#     unique_process_id = os.environ.get("TEST_UNIQUE_PROCESS_ID", None)
#     if not unique_process_id:
#         return False
#
#     remote_debugging_port = os.environ.get("TEST_REMOTE_DEBUGGING_PORT", None)
#     if not remote_debugging_port:
#         return False
#
#     return True


@pytest.mark.skipif(not platform.system().lower() == "windows", reason="requires Windows")
class TestBasic2e2:
    # @pytest.mark.skipif(not is_ready_for_e2e(), reason="requires setup 2e2 environment")
    # @pytest.mark.asyncio
    # async def test_basic(self, task_id: str, unique_process_id: str, remote_debugging_port: int) -> None:
    #     print(task_id, unique_process_id, remote_debugging_port)
    #     async with BrowserAutomator(
    #         remote_debugging_port=remote_debugging_port, unique_process_id=unique_process_id
    #     ) as automator:
    #         ws_endpoint = automator.get_ws_endpoint()
    #
    #         assert ws_endpoint is not None
    #         assert ws_endpoint.startswith("ws://")
    #
    #         assert automator.browser_version is not None
    #         assert automator.browser_version.startswith("Chrome/")
    #         print(automator.browser_version)
    #
    #         await automator.page.goto("https://playwright.dev/python/")
    #         elem = automator.page.locator("xpath=//a[@class='getStarted_Sjon']")
    #         await automator.bas_move_mouse_to_elem(elem=elem)
    #         await elem.click()
    #
    #         page_content = await automator.bas_get_page_content()
    #
    #         assert page_content is not None
    #         assert "html" in page_content

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
