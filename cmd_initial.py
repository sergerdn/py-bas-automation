"""
This script facilitates the integration between BAS (Browser Automation Studio) and `py-bas-automation`.
It handles the creation of browser profiles using FingerprintSwitcher and manages tasks associated with these profiles.
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
    Initialize and run the script.

    :param fingerprint_key: Personal fingerprint key from FingerprintSwitcher.
    :param count_profiles: Number of profiles to be created.

    :return: Path to the generated tasks file.
    """

    # Initialize task storage with read-write access and clear it.
    # The default storage location is C:\Users\{username}\AppData\Local\PyBASTasks
    task_storage = TaskStorage(mode=TaskStorageModeEnum.READ_WRITE)
    task_storage.clear()

    # Initialize browser profiles using the given fingerprint key.
    # The default profile storage location is C:\Users\{username}\AppData\Local\PyBASProfiles
    browser_profile_storage = BrowserProfileStorage(fingerprint_key=fingerprint_key)

    needs = count_profiles - browser_profile_storage.count()

    # Create any additional profiles if necessary
    if needs > 0:
        for _ in range(needs):
            browser_profile = browser_profile_storage.new()
            logger.debug("Created new profile: %s", browser_profile.profile_dir)

    # Generate tasks corresponding to each profile
    for browser_profile in browser_profile_storage.load_all()[:count_profiles]:
        task = BasTask()
        task.browser_settings.profile.profile_folder_path = browser_profile.profile_dir
        task_storage.save(task=task)

    logger.info("Total tasks generated: %d", task_storage.count())
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
    help="Number of profiles.",
    default=10,
)
def main(bas_fingerprint_key: str, count_profiles: int) -> None:
    """
    Entry point of the script. Sets up logging, validates the fingerprint key,
    triggers the primary function, and prints the path to the tasks file.

    :param bas_fingerprint_key: Personal fingerprint key from FingerprintSwitcher.
    :param count_profiles: Number of profiles to be created.

    :return: None.
    """

    import multiprocessing  # pylint: disable=import-outside-toplevel

    process = multiprocessing.current_process()

    # Configure logging settings
    logging.basicConfig(
        level=logging.DEBUG,
        format=f"%(asctime)s {process.pid} %(levelname)s %(name)s %(message)s",
        filename=os.path.join(os.path.dirname(__file__), "logs", "cmd_initial.log"),
    )
    logger.info("Script cmd_initial has started.")

    # Ensure the fingerprint key is present
    bas_fingerprint_key = bas_fingerprint_key.strip()
    if not bas_fingerprint_key:
        raise ValueError("bas_fingerprint_key is not provided")

    # Invoke the main function to get the path to the tasks file
    task_file_path = run(fingerprint_key=bas_fingerprint_key, count_profiles=count_profiles)

    # Print the path for potential use in BAS
    print(json.dumps({"tasks_file": str(task_file_path)}, indent=4))

    logger.info("cmd_initial script execution completed.")


if __name__ == "__main__":
    main()  # pylint: disable=no-value-for-parameter
