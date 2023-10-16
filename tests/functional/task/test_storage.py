import os
import tempfile
from typing import List
from uuid import UUID, uuid4

import pytest
from _pytest.monkeypatch import MonkeyPatch
from pydantic import DirectoryPath, FilePath

from pybas_automation.bas_actions.browser.proxy import BasActionBrowserProxy, BasActionBrowserProxyTypeEnum
from pybas_automation.browser_profile import BrowserProfileStorage
from pybas_automation.browser_profile.models import BrowserProfile
from pybas_automation.task import BasTask, TaskDuplicateError, TaskStorage, TaskStorageModeEnum


def create_task(profiles_dir: DirectoryPath, fingerprint_str: str, with_proxy: bool = False) -> BasTask:
    """Creates a temporary directory for a browser profile"""

    one_profile_dir = DirectoryPath(tempfile.mkdtemp(prefix="profile_", dir=profiles_dir))
    browser_profile = BrowserProfile(profile_dir=one_profile_dir)

    task = BasTask()

    # Set the fingerprint for the browser profile
    browser_profile.fingerprint_raw = fingerprint_str
    browser_profile_storage = BrowserProfileStorage()
    if with_proxy:
        proxy = BasActionBrowserProxy(
            server="127.0.0.1",
            port=9999,
            type=BasActionBrowserProxyTypeEnum.HTTP,
            login="user",
            password="pass",
        )
        browser_profile.proxy = proxy

    # Save the browser profile
    browser_profile_storage.save(browser_profile=browser_profile)
    task.browser_settings.profile.profile_folder_path = browser_profile.profile_dir
    task.browser_settings.proxy = browser_profile.proxy

    return task


class TestTaskStorage:
    def test_fail_storage_dir(self) -> None:
        """
        # Test if initializing TaskStorage with an invalid directory raises a ValueError
        """
        storage_dir = DirectoryPath("some_dir")
        with pytest.raises(ValueError):
            TaskStorage(storage_dir=storage_dir)

        monkeypatch = MonkeyPatch()
        monkeypatch.setenv("LOCALAPPDATA", "some_dir")

        try:
            with pytest.raises(ValueError):
                TaskStorage()
        finally:
            monkeypatch.undo()

    def test_custom_task_filename(self, storage_dir: DirectoryPath, profiles_dir: DirectoryPath) -> None:
        """
        Test if using a custom task filename works as expected.
        """
        task_storage = TaskStorage(task_filename=FilePath("custom_tasks.json"))
        assert task_storage.get_all() is None

    def test_failed_custom_task_filename(self, storage_dir: DirectoryPath, profiles_dir: DirectoryPath) -> None:
        """
        Test if initializing TaskStorage with an invalid custom filename raises a ValueError.
        """
        with pytest.raises(ValueError):
            TaskStorage(task_filename=FilePath(os.path.join("some_dir", "custom_tasks.json")))

    def tests_default_storage_dir(self, storage_dir: DirectoryPath) -> None:
        """
        Test if initializing TaskStorage with the default storage directory works as expected.
        """

        os.environ["LOCALAPPDATA"] = str(storage_dir)
        task_storage = TaskStorage()
        assert task_storage.get_all() is None

    def test_read_mode(self, storage_dir: DirectoryPath, profiles_dir: DirectoryPath, fingerprint_str: str) -> None:
        """
        Test the read-only mode of the TaskStorage.

        This test ensures that the read-only mode of TaskStorage prohibits any write operations
        while still allowing for the tasks to be loaded and read.
        """
        # Initialize TaskStorage in read-only mode and read-write mode
        task_storage_read_mode = TaskStorage(storage_dir=storage_dir, mode=TaskStorageModeEnum.READ)
        task_storage_write_mode = TaskStorage(storage_dir=storage_dir, mode=TaskStorageModeEnum.READ_WRITE)

        # Assert that initially, the read mode storage is empty
        assert task_storage_read_mode.get_all() is None
        task_storage_read_mode.load_all()

        # Test that clear operation raises a ValueError in read mode
        with pytest.raises(ValueError):
            assert task_storage_read_mode.clear()

        # Create a new task for testing
        task = create_task(profiles_dir=profiles_dir, fingerprint_str=fingerprint_str)
        assert task is not None

        # Test that save operation raises a ValueError in read mode
        with pytest.raises(ValueError):
            task_storage_read_mode.save(task=task)

        # Save the task in write mode and then load it in read mode
        task_storage_write_mode.save(task=task)
        task_storage_read_mode.load_all()

        # Check that the read mode storage now contains the task
        assert task_storage_read_mode.get_all() is not None
        assert task_storage_read_mode.count() == 1

        # Test again that clear operation raises a ValueError in read mode
        with pytest.raises(ValueError):
            assert task_storage_read_mode.clear()

    def test_saved(self, storage_dir: DirectoryPath, profiles_dir: DirectoryPath, fingerprint_str: str) -> None:
        """
        Test that tasks are saved and can be retrieved from the storage.

        This test checks the ability to save a task in write mode and then retrieve it in read mode.
        Additionally, it tests that attempting to save in read-only mode raises an error.
        """

        # Initialize TaskStorage in write mode
        task_storage_write = TaskStorage(storage_dir=storage_dir, mode=TaskStorageModeEnum.READ_WRITE)

        # Create a new task and save it in write mode
        task = create_task(profiles_dir=profiles_dir, fingerprint_str=fingerprint_str)
        assert task is not None
        task_storage_write.save(task=task)

        # Initialize TaskStorage in read mode and load tasks
        task_storage_read = TaskStorage(storage_dir=storage_dir, mode=TaskStorageModeEnum.READ)
        assert task_storage_read.load_all() is True

        # Ensure the tasks are loaded and is of the correct type
        assert task_storage_read.get_all() is not None
        assert isinstance(task_storage_read.get_all(), List)

        # Check if the task is present in the storage
        tasks = task_storage_read.get_all()
        assert task in tasks  # type: ignore
        assert task_storage_read.count() == 1

        # Create another new task for testing
        new_task = create_task(profiles_dir=profiles_dir, fingerprint_str=fingerprint_str)
        assert new_task is not None

        # Test that save operation raises a ValueError in read mode and that the count remains unchanged
        with pytest.raises(ValueError):
            task_storage_read.save(task=new_task)
        assert task_storage_read.count() == 1

    def test_basic(self, storage_dir: DirectoryPath, profiles_dir: DirectoryPath, fingerprint_str: str) -> None:
        """
        Test basic functionality of TaskStorage.

        This test checks:
        - Initialization of an empty storage
        - Basic storage operations such as saving and loading of tasks
        - The correct handling of duplicate tasks
        """

        # Initialize TaskStorage in read-write mode and ensure it's empty
        task_storage = TaskStorage(storage_dir=storage_dir, mode=TaskStorageModeEnum.READ_WRITE)
        assert task_storage.get_all() is None
        assert task_storage.count() == 0

        # Verify that saving an empty list of tasks raises a ValueError
        with pytest.raises(ValueError):
            task_storage.save_all()

        # Confirm that clearing and loading an empty storage returns False
        assert task_storage.clear() is False  # no tasks to clear
        assert task_storage.load_all() is False  # no tasks to load

        # Create and save multiple tasks
        tasks_id = []
        for _ in range(0, 10):
            task = create_task(profiles_dir=profiles_dir, fingerprint_str=fingerprint_str)
            assert task is not None
            assert isinstance(task, BasTask)
            task_storage.save(task=task)
            tasks_id.append(str(task.task_id))

        # Ensure all tasks are saved successfully
        assert task_storage.save_all() is True

        # Validate that each saved task can be retrieved
        for one in tasks_id:
            exists_task = task_storage.get(task_id=UUID(one))
            assert exists_task is not None
            assert isinstance(exists_task, BasTask)

        # Confirm tasks are loaded and storage is in expected state
        assert task_storage.load_all() is True
        assert task_storage.get_all() is not None
        assert isinstance(task_storage.get_all(), List)
        assert len(task_storage.get_all()) == 10  # type: ignore
        assert task_storage.count() == 10
        assert task_storage.get(task_id=uuid4()) is False  # Ensure a random ID doesn't return a task

        # Validate that clearing the storage works and the count is zero
        assert task_storage.clear() is True
        assert task_storage.count() == 0
        assert task_storage.load_all() is False  # No tasks to load after clearing
        assert task_storage.get(task_id=uuid4()) is False  # No tasks to retrieve after clearing

        # Verify handling of duplicate tasks
        task = create_task(profiles_dir=profiles_dir, fingerprint_str=fingerprint_str)
        task_storage.save(task=task)
        with pytest.raises(TaskDuplicateError):
            task_storage.save(task=task)

        # Representation of task storage (for debug purposes)
        print(task_storage)  # repr

    def test_proxy(self, storage_dir: DirectoryPath, profiles_dir: DirectoryPath, fingerprint_str: str) -> None:
        """
        Test the saving functionality of TaskStorage with a task that uses a proxy.

        This test checks:
        - Creation of a task with proxy settings
        - The proper presence of proxy settings in the created task
        - Saving the proxy-enabled task in storage
        """

        # Initialize TaskStorage in read-write mode for saving tasks
        task_storage_write = TaskStorage(storage_dir=storage_dir, mode=TaskStorageModeEnum.READ_WRITE)

        # Create a task with proxy settings enabled
        task = create_task(profiles_dir=profiles_dir, fingerprint_str=fingerprint_str, with_proxy=True)

        # Validate the presence of proxy settings in the created task
        assert task.browser_settings.proxy is not None
        assert task is not None

        # Save the task with proxy settings to the storage
        task_storage_write.save(task=task)
