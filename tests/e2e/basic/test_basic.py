import os

import pytest

from pybas_automation.browser_automator import BrowserAutomator


def is_ready_for_e2e() -> bool:
    task_id = os.environ.get("TEST_TASK_ID", None)
    if not task_id:
        return False

    unique_process_id = os.environ.get("TEST_UNIQUE_PROCESS_ID", None)
    if not unique_process_id:
        return False

    remote_debugging_port = os.environ.get("TEST_REMOTE_DEBUGGING_PORT", None)
    if not remote_debugging_port:
        return False

    return True


@pytest.mark.skipif(not is_ready_for_e2e(), reason="requires setup 2e2 environment")
class TestBasic2e2:
    @pytest.mark.asyncio
    async def test_basic(self, task_id: str, unique_process_id: str, remote_debugging_port: int) -> None:
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
