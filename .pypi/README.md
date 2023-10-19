# py-bas-automation

[![Linux Python CI](https://github.com/sergerdn/py-bas-automation/actions/workflows/ci_linux.yml/badge.svg)](https://github.com/sergerdn/py-bas-automation/actions/workflows/ci_linux.yml)
[![Windows Python CI](https://github.com/sergerdn/py-bas-automation/actions/workflows/ci_windows.yml/badge.svg)](https://github.com/sergerdn/py-bas-automation/actions/workflows/ci_windows.yml)
[![codecov](https://codecov.io/gh/sergerdn/py-bas-automation/graph/badge.svg?token=YQYHYG9VVM)](https://codecov.io/gh/sergerdn/py-bas-automation)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Note: This library is currently in active development, and its API may undergo changes without notice at any time.**

**Note:** This project originally started as a `working proof of concept` and does not aim to offer extensive support or
documentation. It serves as a fundamental demonstration of the concept and should be considered a foundation for further
development or experimentation.

## Description

This library enables you to work with BAS (BrowserAutomationStudio) using headless Chromium browsers and a
customizable Windows GUI program, while controlling it with Python ❤️.
![bas_gui_window_3.png](https://sergerdn.github.io/py-bas-automation/images/bas_gui_window_3.png)

## Key Features

- **BrowserAutomationStudio Integration:** Run BAS seamlessly with headless browsers while enjoying the convenience of a
  user-friendly and customizable Windows GUI program
  through [BrowserAutomationStudio](https://bablosoft.com/shop/BrowserAutomationStudio).
- **Unique Fingerprint Feature:** The application includes a unique feature that assigns a  `fingerprint`  to each
  browser instance using [FingerprintSwitcher](https://fingerprints.bablosoft.com/). Please be aware that this is
  **paid** service.
- **Proxy Support:** The application supports proxy providers such as [Brightdata](https://brightdata.com/). Please
  note that this is a **paid** service.
- **Executing Browser Automation Studio (BAS) Actions from Python**: Implement BAS actions from Python using the
  un-documented API. This includes actions such as retrieving page source, `emulating mouse movements`, etc. (Note: Not
  all functions are currently supported).
- **Playwright Control:** The application leverages [Playwright](https://playwright.dev/python/) to efficiently manage
  and control BAS.

## Understanding the Workflow

The functioning of BAS (Browser Automation Studio) involves the following steps:

1. **Initial Execution:** Upon initiation, BAS runs [cmd_initial.py](https://github.com/sergerdn/py-bas-automation/blob/develop/cmd_initial.py). This script is responsible for
   creating tasks and storing them on the disk for later use.
2. **Data Acquisition and Browser Configuration:** BAS then retrieves the necessary data, configures, and launches
   browser instances based on the tasks provided earlier.
3. **Task Execution:** Following the browser setup, BAS executes [cmd_worker.py](https://github.com/sergerdn/py-bas-automation/blob/develop/cmd_worker.py) using the  `task_id`
   and  `remote-debugging-port`  number as command-line parameters.
4. **Task Handling:** [cmd_worker.py](https://github.com/sergerdn/py-bas-automation/blob/develop/cmd_worker.py) obtains both the  `ws_endpoint`  and  `remote-debugging-port`
   from the command line. It then manages complex tasks using [Playwright](https://playwright.dev/python/). These tasks
   can range from opening a webpage to filling out forms or even taking screenshots.
5. **Task Completion:** Once the tasks have been completed, BAS terminates the browser instances and exits.

The result of running [cmd_worker.py](https://github.com/sergerdn/py-bas-automation/blob/develop/cmd_worker.py) is as follows:

```json
{
  "tasks_file": "C:\\Users\\Administrator\\AppData\\Local\\PyBASProfilesTasks\\tasks.json"
}
```

This is an example of the created `tasks_file`:

```json
[
  {
    "task_id": "9683607e-2458-4adb-9b14-7e99123bf34d",
    "browser_settings": {
      "components": {
        "widevine": "enable",
        "safe_browsing": "enable",
        "components": "enable"
      },
      "network": {
        "enable_qiuc_protocol": true
      },
      "rendering": {
        "maximum_fps": 30
      },
      "browser_version": "default",
      "command_line": [
        "--disk-cache-size=104857600",
        "--disable-gpu-program-cache",
        "--disable-gpu-shader-disk-cache",
        "--disable-features=GpuProcessHighPriorityWin,GpuUseDisplayThreadPriority",
        "--lang=en"
      ],
      "profile": {
        "profile_folder_path": "C:\\Users\\Administrator\\AppData\\Local\\PyBASProfiles\\tmp3az8nj96",
        "always_load_fingerprint_from_profile_folder": false,
        "always_load_proxy_from_profile_folder": false
      },
      "proxy": {
        "server": "brd.superproxy.io",
        "port": "22225",
        "type": "http",
        "login": "brd-customer-hl___redacted__",
        "password": "__redacted__"
      },
      "fingerprint": {
        "safe_canvas": true,
        "use_perfect_canvas": true,
        "safe_webgl": true,
        "safe_audio": true,
        "safe_battery": true,
        "use_font_pack": true,
        "safe_element_size": false,
        "emulate_sensor_api": true,
        "emulate_device_scale_factor": true
      }
    }
  }
]
```

This file contains task details such as browser settings, network configurations, rendering options, and fingerprint
settings, among other things.

## System Requirements

For the optimal running of this application, the following system requirements are necessary:

- **Operating System:** The application is compatible with Windows 10/11 and Windows Server 2022 (tested on 21H2).
- **Python:** Ensure you have Python 3.11 or higher installed. If not, you can download it from the official
  Python [website](https://www.python.org/downloads/).
- **Poetry:** This is a necessary tool for managing Python dependencies. You can find the installation guide on the
  official Poetry [documentation](https://python-poetry.org/docs/#installation).
- **Git:** The application requires Git for version control. If it's not already installed on your system, you can
  download it from the official Git [website](https://git-scm.com/downloads).
- **Make:** This is an optional tool, it can be downloaded from the
  Chocolatey [website](https://community.chocolatey.org/packages/make).
- **FingerprintSwitcher License:** Please note that this is a **paid** feature. You will need a valid license
  for [FingerprintSwitcher](https://fingerprints.bablosoft.com/) to access its functionalities.

## Installation Guide

### Installing the Current Development Version

To work with the most recent development version of `pybas-automation`, follow the steps outlined below:

1. **Clone the Repository:** Clone the  `py-bas-automation`  repository from GitHub.
2. **Navigate to the Directory:** Once cloned, navigate to the  `py-bas-automation`  directory on your local system.
3. **Install Dependencies:** With Poetry, install all the necessary dependencies.

Here are the corresponding commands for each step:

```bash
git clone git@github.com:sergerdn/py-bas-automation.git
cd py-bas-automation
git lfs pull
poetry install
```

### Installing the Latest Release from pypi.org (Currently not recommended)

If you wish to incorporate  `pybas-automation`  into your project, execute the following command:

```bash
poetry add pybas-automation
```

Please note that this is not currently recommended as the latest release may have unresolved issues.

## How to Run the Application

- **Download the BAS Program:** Begin by downloading the latest version of the compiled BAS program,
  called  `PyBasFree.zip` . You can find this file in the project directory
  under [PyBasFree.zip](https://github.com/sergerdn/py-bas-automation/blob/develop/bas_release/PyBasFree.zip). After downloading, extract the contents and
  execute  `PyBasFree.exe`.
- **Set Variables in the BAS GUI:** After running the BAS program, proceed to set the necessary variables within the
  BAS graphical user interface (GUI).
  ![BAS GUI](https://sergerdn.github.io/py-bas-automation/images/bas_gui_window_1.png)
- **Set Up Proxy Provider:**  If you are using a proxy provider, you will need to configure it within the BAS GUI. This
  can be accomplished by navigating to the `Proxy Settings` option in the vertical menu and selecting the appropriate
  provider.
  ![Set up proxy provider](https://sergerdn.github.io/py-bas-automation/images/bas_gui_window_1_proxy.png)
- **Start the Program:** Once all variables have been set, click the "OK" button to initiate the program.
  ![Start Program](https://sergerdn.github.io/py-bas-automation/images/bas_gui_window_2.png)

## Advanced Usage

This guide introduces a Python script that integrates the `Browser Automation Studio` (BAS) with `py-bas-automation`.
The
purpose is to handle the creation of browser profiles through FingerprintSwitcher and manage tasks related to these
profiles.

### [Initial script: cmd_initial.py](https://github.com/sergerdn/py-bas-automation/blob/develop/cmd_initial.py)

### Description:

This script facilitates the integration between `BAS (Browser Automation Studio)` and `py-bas-automation`. It manages
the creation of browser profiles using `FingerprintSwitcher` and generates tasks associated with these profiles.

### Overview:

- **Initialization**: Import essential modules and configure logging.
- **Browser Profiles**: Utilize `FingerprintSwitcher`'s fingerprint key to generate or manage browser profiles.
- **Proxy Support**: Configure proxy settings for each browser profile in full-automatic mode by handling proxy
  providers. Note: at the moment only [`Brightdata`](https://brightdata.com/) is supported.
- **Tasks Generation**: Generate an associated task for each browser profile and store it.

```python
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

    import multiprocessing

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
    main()
```

### [Worker script: cmd_worker.py](https://github.com/sergerdn/py-bas-automation/blob/develop/cmd_worker.py)

### Description:

This script demonstrates how to execute tasks using the `Playwright` Python library in conjunction with the
`pybas_automation` package. The primary goal is to fetch task data, connect to an existing browser instance using
`Playwright`, and perform actions on a webpage.

### Overview:

- **Initialization**: Import necessary libraries and set up our task id and debugging port.
- **Task Storage**: Fetch a specific task from our task storage.
- **Remote Browser Connection**: Use the remote debugging port to get a WebSocket endpoint, which allows us to connect
  to an existing browser instance.
- **Executing Browser Automation Studio (BAS) Actions from Python**: Implement BAS actions from Python using the
  un-documented API. This includes actions such as retrieving page source, emulating mouse movements, etc. (Note: Not
  all functions are currently supported).

```python
import asyncio
from uuid import UUID
from playwright.async_api import async_playwright
from pybas_automation.task import TaskStorage, TaskStorageModeEnum
from pybas_automation.browser_automator import BrowserAutomator


async def main():
    # 1. Initialization
    # For demonstration purposes, we're using hardcoded values. In a real scenario, these will be fetched dynamically.
    task_id = UUID("some_task_id_that_we_getting_from_cmd_line_from_BAS")
    remote_debugging_port = 9222
    # A unique identifier for the `Worker.exe` process. Retrieved from the command line  argument `--unique-process-id`.
    unique_process_id = "some_unique_process_id"

    # 2. Task Storage
    # Create a new task storage instance in READ mode to fetch tasks.
    task_storage = TaskStorage(mode=TaskStorageModeEnum.READ)
    found_task = task_storage.get(task_id=task_id)
    # Note: You can manipulate or inspect the `found_task` as needed.

    # 3. Remote Browser Connection
    async with BrowserAutomator(
            remote_debugging_port=remote_debugging_port, unique_process_id=unique_process_id
    ) as automator:
        # Variant 1: Work with the BrowserAutomator API
        await automator.page.goto("https://playwright.dev/python/")
        if unique_process_id:
            # With Automator, you can call function from the BrowserAutomationStudio API.
            print("Unique process ID: %s", unique_process_id)
            page_content = await automator.bas_get_page_content()

            elem = automator.page.locator("xpath=//a[@class='getStarted_Sjon']")
            await automator.bas_move_mouse_to_elem(elem=elem)
            await elem.click()

            print("Page content from BAS_SAFE api: %s ...", page_content[:100])

        # Variant 1: Work with the Playwright API directly.
        ws_endpoint = automator.get_ws_endpoint()
        async with async_playwright() as pw:
            # Connect to an existing browser instance using the fetched WebSocket endpoint.
            browser = await pw.chromium.connect_over_cdp(ws_endpoint)
            # Access the main page of the connected browser instance.
            page = browser.contexts[0].pages[0]
            # Perform actions using Playwright, like navigating to a webpage.
            await page.goto("https://playwright.dev/python/")


if __name__ == "__main__":
    asyncio.run(main())
```

## Planned Improvements:

- [x] Add Proxy support.
- [x] Develop end-to-end tests to thoroughly assess the entire workflow.
- [ ] Include build scripts for converting Python files to executable format.
- [ ] Expand the repository with more illustrative examples.

## Contributing

Your ideas and contributions are highly valued. Please do not hesitate to open
an [issue](https://github.com/sergerdn/py-bas-automation/issues/new) if you have suggestions, questions, or if you would
like to contribute to its enhancement.

## License

[LICENSE](https://github.com/sergerdn/py-bas-automation/blob/develop/LICENSE)

