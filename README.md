# py-bas-automation

**Note:** This project originally started as a `working proof of concept` and does not aim to offer extensive support or
documentation. It serves as a fundamental demonstration of the concept and should be considered a foundation for further
development or experimentation.

## Description

This library enables you to work with BAS (BrowserAutomationStudio) using headless Chromium browsers and a
customizable Windows GUI program, while controlling it with Python ❤️.
![bas_gui_window_3.png](docs/images/bas_gui_window_3.png)

## Features

- Run BAS with headless browsers and a user-friendly, customizable Windows GUI program (BrowserAutomationStudio).
- It includes a unique feature that provides a `fingerprint` for each browser instance
  using [FingerprintSwitcher](https://fingerprints.bablosoft.com/). Please note, this is a **paid** feature.
- Utilize [Playwright](https://playwright.dev/python/) to control BAS.

## How it works

When BAS starts, it executes [cmd_initial.py](./cmd_initial.py), which creates tasks and saves them to disk.
Subsequently, BAS obtains data, configures, and initiates a browser instances with the provided tasks.

Afterward, BAS runs [cmd_worker.py](./cmd_worker.py) with the `task_id` and the `remote-debugging-port` number as
command-line parameters.

[cmd_worker.py](./cmd_worker.py) retrieves both the `ws_endpoint` and `remote-debugging-port` from the command line and
handles complex tasks using  [Playwright](https://playwright.dev/python/). For example, it can open a page, fill out a
forms, make screenshot, etc.

## Requirements

- Windows 10/11, Windows Server 2022(tested on 21H2).
- Python 3.11+ (https://www.python.org/downloads/).
- Poetry (https://python-poetry.org/docs/#installation).
- Git (https://git-scm.com/downloads).
- Make (https://chocolatey.org/packages/make) - optional.
- A license for [FingerprintSwitcher](https://fingerprints.bablosoft.com/). This is a **paid** feature.

## Installation

- Checkout the latest version of `py-bas-automation` to the current project with [Poetry](https://python-poetry.org/):

```bash
git clone git@github.com:sergerdn/py-bas-automation.git
cd py-bas-automation
poetry install
```

- Download the latest compiled BAS program from [Releases](https://github.com/sergerdn/py-bas-automation/releases).

## Running

- Run the downloaded BAS program and set variables in the BAS GUI.
  ![bas_gui_window_1.png](docs/images/bas_gui_window_1.png)
- Click "OK" button to start program.
  ![bas_gui_window_2.png](docs/images/bas_gui_window_2.png)

## Advanced Usage

Here's a basic example of using `py-bas-automation`:

- [Initial script](./cmd_initial.py) to create tasks:

```python
import json
from pybas_automation.task import BasTask, TaskStorage, TaskStorageModeEnum
from pybas_automation.browser_profile import BrowserProfileStorage

fingerprint_key = "your_fingerprint_key"

# Create a new task
task = BasTask()

# Save the task to storage, default location is
# C:\Users\{username}\AppData\Local\PyBASTasks
task_storage = TaskStorage(mode=TaskStorageModeEnum.READ_WRITE)
task_storage.save(task)

# Initialize a browser profile storage, default location is 
# C:\Users\{username}\AppData\Local\PyBASProfiles
browser_profile_storage = BrowserProfileStorage(fingerprint_key=fingerprint_key)

# Create 20 fresh profiles on disk
for _ in range(0, 20):
    browser_profile = browser_profile_storage.new()

# Add created browser profiles to tasks
for browser_profile in browser_profile_storage.load_all():
    task = BasTask()
    task.browser_settings.profile.profile_folder_path = browser_profile.profile_dir
    task_storage.save(task=task)

task_file_path = task_storage.task_file_path

# print path to tasks file for use it in BAS
print(json.dumps({"tasks_file": str(task_file_path)}, indent=4))
```

- [Worker script](./cmd_worker.py) to retrieve the ws_endpoint from bas and handle the complex tasks:

```python
from uuid import UUID
from playwright.sync_api import sync_playwright
from pybas_automation.task import BasTask, TaskStorage, TaskStorageModeEnum
from pybas_automation.browser_remote import BrowserRemote

# skip code to getting ws_endpoint from cmd line ...
task_id = UUID("some_task_id_that_we_getting_from_cmd_line_from_BAS")

# Create a new task storage
task_storage = TaskStorage(mode=TaskStorageModeEnum.READ)
found_task = task_storage.get(task_id=task_id)
# Do something with task if needed...
# Save the task to storage, default location is

# Skip code to getting remote_debugging_port from cmd line ...
remote_debugging_port = 9222

remote_browser = BrowserRemote(remote_debugging_port=remote_debugging_port)

# Get ws_endpoint from remote_debugging_port
remote_browser.find_ws()
ws_endpoint = remote_browser.ws_endpoint

with sync_playwright() as pw:
    # Connect to an existing browser instance
    browser = pw.chromium.connect_over_cdp(ws_endpoint)
    # Get the existing pages in the connected browser instance
    page = browser.contexts[0].pages[0]
    # Doing some work with page
    page.goto("https://playwright.dev/python/")
```

## Contributing

Your ideas and contributions are highly valued. Please do not hesitate to open
an [issue](https://github.com/sergerdn/py-bas-automation/issues/new) if you have suggestions, questions, or if you
would like to contribute to its enhancement.