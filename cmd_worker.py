"""
This script manages task executions.

It retrieves task specifics from BAS, runs the corresponding Playwright script, and then saves
the produced screenshots to the `reports` folder.
"""

import asyncio
import json
import logging
import os
from uuid import UUID

import click
from dotenv import load_dotenv
from playwright.async_api import async_playwright

from pybas_automation.browser_remote import BrowserRemote
from pybas_automation.task import BasTask, TaskStorage, TaskStorageModeEnum

# Load environment variables
load_dotenv()

logger = logging.getLogger("[cmd_worker]")
_debug = os.environ.get("DEBUG", "False").lower() == "true"


async def run(task_id: UUID, remote_debugging_port: int) -> None:
    """
    Fetch the specified task and run the associated worker.

    :param task_id: Unique identifier of the desired task.
    :param remote_debugging_port: Port used for Chrome DevTools Protocol (CDP) remote debugging.

    :return: None.
    """

    # Validate input parameters
    if not task_id:
        raise ValueError("task_id is not provided")
    if not remote_debugging_port:
        raise ValueError("remote_debugging_port is not provided")

    logger.debug("Retrieving task with ID: %s", task_id)

    task_storage = TaskStorage(mode=TaskStorageModeEnum.READ)

    # Ensure there are tasks to load
    if not task_storage.load_all():
        raise ValueError("No tasks available for processing")

    # Fetch the specified task
    found_task = task_storage.get(task_id=task_id)
    if not found_task:
        raise ValueError(f"Task with ID {task_id} not found")

    # Debug: Print the task details
    print(json.dumps(found_task.model_dump(mode="json"), indent=4))

    profile_folder_path = found_task.browser_settings.profile.profile_folder_path
    remote_browser = BrowserRemote(remote_debugging_port=remote_debugging_port)
    remote_browser.find_ws()

    if not remote_browser.ws_endpoint:
        raise ValueError(f"Unable to fetch websocket endpoint for profile: {profile_folder_path}")

    await work(remote_browser.ws_endpoint, found_task)


async def work(ws_endpoint: str, task: BasTask) -> None:
    """
    Execute a Playwright script to capture a screenshot.

    :param ws_endpoint: WebSocket endpoint used to connect to the browser.
    :param task: Instance of the task to be processed.

    :return: None.
    """

    async with async_playwright() as pw:
        browser = await pw.chromium.connect_over_cdp(ws_endpoint)
        page = browser.contexts[0].pages[0]

        # Navigate to the Playwright documentation and wait for it to load
        await page.goto("https://playwright.dev/python/")
        await asyncio.sleep(5)

        # Save a screenshot of the current page
        screenshot_filename = os.path.join(os.path.dirname(__file__), "reports", f"{task.task_id}_screenshot.png")
        await page.screenshot(path=screenshot_filename, full_page=True)


@click.command()
@click.option("--task_id", help="Unique identifier of the task.", required=True)
@click.option(
    "--remote_debugging_port",
    help="Port number used for Chrome DevTools Protocol (CDP) remote debugging.",
    type=int,
    required=True,
)
def main(task_id: UUID, remote_debugging_port: int) -> None:
    """
    Set up logging and initiate the task execution process.

    :param task_id: Unique identifier of the task.
    :param remote_debugging_port: Port used for CDP remote debugging.

    :return: None.
    """

    import multiprocessing  # pylint: disable=import-outside-toplevel

    process = multiprocessing.current_process()

    # Logging configuration
    logging.basicConfig(
        level=logging.DEBUG,
        format=f"%(asctime)s {process.pid} %(levelname)s %(name)s %(message)s",
        filename=os.path.join(os.path.dirname(__file__), "logs", "cmd_worker.log"),
    )

    logger.info("Initializing cmd_worker with PID: %s", process.pid)

    asyncio.run(run(task_id=task_id, remote_debugging_port=remote_debugging_port))


if __name__ == "__main__":
    main()  # pylint: disable=no-value-for-parameter
