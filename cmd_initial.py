"""
Initial script to create tasks and profiles if needed.
"""

import json
import logging
import os

import click
from pydantic import FilePath

from pybas_automation.browser_profile import BrowserProfileStorage
from pybas_automation.task import BasTask, TaskStorage, TaskStorageModeEnum

logger = logging.getLogger("[cmd_worker]")


def run(fingerprint_key: str, count_profiles: int) -> FilePath:
    """
    Run initial script.

    :param fingerprint_key: Your personal fingerprint key of FingerprintSwitcher.
    :param count_profiles:  Count profiles to be created.

    :return: Path to the tasks file.
    """

    task_storage = TaskStorage(mode=TaskStorageModeEnum.READ_WRITE)
    task_storage.clear()

    browser_profile_storage = BrowserProfileStorage(fingerprint_key=fingerprint_key)
    needs = count_profiles - browser_profile_storage.count()

    if needs > 0:
        for _ in range(0, needs):
            browser_profile = browser_profile_storage.new()
            logger.debug("Created new profile: %s", browser_profile.profile_dir)

    for browser_profile in browser_profile_storage.load_all()[:count_profiles]:
        task = BasTask()
        task.browser_settings.profile.profile_folder_path = browser_profile.profile_dir
        task_storage.save(task=task)

    logger.info("Count tasks: %d", task_storage.count())
    task_storage.save_all()

    return task_storage.task_file_path


@click.command()
@click.option(
    "--bas_fingerprint_key",
    help="Your personal fingerprint key of FingerprintSwitcher.",
    required=True,
)
@click.option(
    "--count_profiles",
    help="Count profiles.",
    default=10,
)
def main(bas_fingerprint_key: str, count_profiles: int) -> None:
    """
    Main function.

    :param bas_fingerprint_key: Your personal fingerprint key of FingerprintSwitcher.
    :param count_profiles: Count profiles to be created.

    :return: None.
    """

    import multiprocessing  # pylint: disable=import-outside-toplevel

    process = multiprocessing.current_process()

    logging.basicConfig(
        level=logging.DEBUG,
        format=f"%(asctime)s {process.pid} %(levelname)s %(name)s %(message)s",
        filename=os.path.join(os.path.dirname(__file__), "logs", "cmd_initial.log"),
    )
    logger.info("Started cmd_initial.")

    bas_fingerprint_key = bas_fingerprint_key.strip()

    if not bas_fingerprint_key:
        raise ValueError("bas_fingerprint_key is not set")

    task_file_path = run(fingerprint_key=bas_fingerprint_key, count_profiles=count_profiles)

    print(json.dumps({"tasks_file": str(task_file_path)}, indent=4))

    logger.info("Finished cmd_initial.")


if __name__ == "__main__":
    main()  # pylint: disable=no-value-for-parameter
