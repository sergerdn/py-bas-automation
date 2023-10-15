"""
This script manages task executions.

It retrieves task specifics from BAS, runs the corresponding Playwright script, and then saves
the produced screenshots to the `reports` folder.
"""

import asyncio
import codecs
import json
import logging
import os
from uuid import UUID

import click
from dotenv import load_dotenv
from playwright.async_api import async_playwright

from pybas_automation.browser_automator import BrowserAutomator
from pybas_automation.task import TaskStorage, TaskStorageModeEnum

# Load environment variables
load_dotenv()

logger = logging.getLogger("[cmd_worker]")
_debug = os.environ.get("DEBUG", "False").lower() == "true"


async def run(task_id: UUID, remote_debugging_port: int, unique_process_id: str) -> None:
    """
    Fetch the specified task and run the associated worker.

    :param task_id: Unique identifier of the desired task.
    :param remote_debugging_port: Port used for Chrome DevTools Protocol (CDP) remote debugging.
    :param unique_process_id: A unique identifier for the `Worker.exe` process. Retrieved from the command line.

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
    screenshot_filename = os.path.join(os.path.dirname(__file__), "reports", f"{found_task.task_id}_screenshot.png")

    async with BrowserAutomator(
        remote_debugging_port=remote_debugging_port, unique_process_id=unique_process_id
    ) as automator:
        # Variant 1: Work with the BrowserAutomator API
        await automator.page.goto("https://playwright.dev/python/")
        if unique_process_id:
            # With Automator, you can call function from the BrowserAutomationStudio API.
            logger.info("Unique process ID: %s", unique_process_id)
            page_content = await automator.bas_get_page_content()
            logger.debug("Page content from BAS_SAFE api: %s ...", page_content[:100])

        # Variant 1: Work with the Playwright API directly.
        ws_endpoint = automator.get_ws_endpoint()
        async with async_playwright() as pw:
            # Connect to an existing browser instance using the fetched WebSocket endpoint.
            browser = await pw.chromium.connect_over_cdp(ws_endpoint)
            # Access the main page of the connected browser instance.
            page = browser.contexts[0].pages[0]
            # Perform actions using Playwright, like navigating to a webpage.
            await page.goto("https://playwright.dev/python/")

            # Save a screenshot of the current page
            await automator.page.screenshot(path=screenshot_filename, full_page=True)


@click.command()
@click.option("--task_id", help="Unique identifier of the task.", required=True)
@click.option(
    "--remote_debugging_port",
    help="Port number used for Chrome DevTools Protocol (CDP) remote debugging.",
    type=int,
    required=True,
)
@click.option("--unique_process_id", help="Unique identifier of the Worker.exe process.")
@click.option(
    "--debug",
    help="Enable debug mode.",
    is_flag=True,
)
def main(
    task_id: UUID,
    remote_debugging_port: int,
    unique_process_id: str,
    debug: bool,
) -> None:
    """
    Set up logging and initiate the task execution process.

    :param task_id: Unique identifier of the task. :param remote_debugging_port: Port used for CDP remote debugging.
    :param remote_debugging_port: Port used for Chrome DevTools Protocol (CDP) remote debugging.
    :param unique_process_id: A unique identifier for the `Worker.exe` process. Retrieved from the command line
    argument `--unique-process-id`.
    :param debug: Enable debug mode.

    :return: None.
    """

    if debug:
        logger.debug("Debug mode enabled")

        # Playwright debug logging
        os.environ["DEBUG"] = "pw:protocol"

        filename = os.path.join(os.path.dirname(__file__), "logs", "cdp_log.txt")
        import sys  # pylint: disable=import-outside-toplevel

        sys.stderr = codecs.open(filename, "w", "utf-8")

    import multiprocessing  # pylint: disable=import-outside-toplevel

    process = multiprocessing.current_process()

    # Logging configuration
    logging.basicConfig(
        level=logging.DEBUG,
        format=f"%(asctime)s {process.pid} %(levelname)s %(name)s %(message)s",
        filename=os.path.join(os.path.dirname(__file__), "logs", "cmd_worker.log"),
    )

    logger.info("Initializing cmd_worker with PID: %s", process.pid)

    asyncio.run(run(task_id=task_id, remote_debugging_port=remote_debugging_port, unique_process_id=unique_process_id))


if __name__ == "__main__":
    main()  # pylint: disable=no-value-for-parameter
