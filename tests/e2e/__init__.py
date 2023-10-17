import asyncio
import os
import shutil
import tempfile

import filelock

FIXTURES_TEMP_DIR = os.path.join(tempfile.gettempdir(), "pybas_automation_tests_e2e_fixtures")
FILE_LOCK_FILENAME = filelock.FileLock(os.path.join(FIXTURES_TEMP_DIR, ".lock"))


async def clean_dir(dir_name: str) -> None:
    """Asynchronously cleans (deletes) the specified directory.

    :param dir_name: The name of the directory to be cleaned.
    """

    # Sleep for a short while before attempting to remove the directory.
    # This might be necessary to let any processes that might be using the directory to release it.
    await asyncio.sleep(5)

    # Attempt to remove the directory. If unsuccessful, retries up to 5 times.
    for _ in range(0, 5):
        try:
            shutil.rmtree(dir_name)
        except Exception as exc:  # type: ignore
            print(exc)
            # Wait for a bit before the next attempt
            await asyncio.sleep(5)
            continue

        # If the directory was successfully removed, break out of the loop
        break

    # As a last attempt, try to remove the directory while ignoring any errors
    shutil.rmtree(dir_name, ignore_errors=True)
