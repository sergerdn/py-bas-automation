"""
This script is responsible for running tasks.
It gets task data from BAS, runs a Playwright script, and saves the screenshots to the `reports` folder.
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

load_dotenv()


logger = logging.getLogger("[cmd_worker]")


_debug = os.environ.get("DEBUG", "False").lower() == "true"


async def run(task_id: UUID, remote_debugging_port: int) -> None:
    """
    Run worker.

    :param task_id: Task id of task.
    :param remote_debugging_port: CDP remote debugging port.♣

    :return: None.
    """

    if not task_id:
        raise ValueError("task_id is not set")

    if not remote_debugging_port:
        raise ValueError("remote_debugging_port is not set")

    logger.debug("getting task_id: %s", task_id)

    task_storage = TaskStorage(mode=TaskStorageModeEnum.READ)

    if not task_storage.load_all():
        raise ValueError("No tasks to load")

    found_task = task_storage.get(task_id=task_id)
    if not found_task:
        raise ValueError(f"Cannot find task for task_id: {task_id}")

    logger.info("Found task for task_id: %s", task_id)

    print(json.dumps(found_task.model_dump(mode="json"), indent=4))

    profile_folder_path = found_task.browser_settings.profile.profile_folder_path

    remote_browser = BrowserRemote(remote_debugging_port=remote_debugging_port)
    remote_browser.find_ws()

    logger.info("Found ws %s for for profile: %s", remote_browser.ws_endpoint, profile_folder_path)
    if not remote_browser.ws_endpoint:
        raise ValueError(f"Cannot get ws endpoint for profile: {profile_folder_path}")

    await work(remote_browser.ws_endpoint, found_task)


async def work(ws_endpoint: str, task: BasTask) -> None:
    """
    Work playwright script to make screenshots.

    :param ws_endpoint: Websocket endpoint.
    :param task: Task instance.

    :return: None.
    """

    logger.debug("ws_endpoint: %s", ws_endpoint)
    async with async_playwright() as pw:
        # Connect to an existing browser instance
        browser = await pw.chromium.connect_over_cdp(ws_endpoint)
        logger.info("Connected to browser: %s", browser)

        # Get the existing pages in the connected browser instance
        page = browser.contexts[0].pages[0]

        task_id = task.task_id

        await page.goto("https://playwright.dev/python/")
        await asyncio.sleep(5)

        current_url = page.url
        logger.debug("current url: %s", current_url)

        # Take a screenshot and save it to the specified file
        screenshot_filename = os.path.join(os.path.dirname(__file__), "reports", f"{task_id}_screenshot.png")
        await page.screenshot(path=screenshot_filename, full_page=True)


@click.command()
@click.option(
    "--task_id",
    help="Task id of task.",
    required=True,
)
@click.option(
    "--remote_debugging_port",
    help="CDP remote debugging port.",
    type=int,
    required=True,
)
def main(task_id: UUID, remote_debugging_port: int) -> None:
    """
    Main function.

    :param task_id: Task id of task.
    :param remote_debugging_port: CDP remote debugging port.

    :return: None.
    """

    import multiprocessing  # pylint: disable=import-outside-toplevel

    process = multiprocessing.current_process()

    logging.basicConfig(
        level=logging.DEBUG,
        format=f"%(asctime)s {process.pid} %(levelname)s %(name)s %(message)s",
        filename=os.path.join(os.path.dirname(__file__), "logs", "cmd_worker.log"),
    )

    logger.info(
        "Started cmd_worker: %s, task_id: %s, remote_debugging_port: %d", process.pid, task_id, remote_debugging_port
    )

    asyncio.run(run(task_id=task_id, remote_debugging_port=remote_debugging_port))


if __name__ == "__main__":
    main()  # pylint: disable=no-value-for-parameter
