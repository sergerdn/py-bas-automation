import os
import shutil
import tempfile
from typing import Generator, List
from uuid import UUID, uuid4

import pytest
from _pytest.monkeypatch import MonkeyPatch
from pydantic import DirectoryPath, FilePath

from pybas_automation.browser_profile import BrowserProfileStorage
from pybas_automation.browser_profile.models import BrowserProfile
from pybas_automation.task import BasTask, TaskDuplicateError, TaskStorage, TaskStorageModeEnum


def create_task(profiles_dir: DirectoryPath, fingerprint_str: str) -> BasTask:
    one_profile_dir = DirectoryPath(tempfile.mkdtemp(prefix="profile_", dir=profiles_dir))
    browser_profile = BrowserProfile(profile_dir=one_profile_dir)

    task = BasTask()

    browser_profile.fingerprint_raw = fingerprint_str
    browser_profile_storage = BrowserProfileStorage()
    browser_profile_storage.save(browser_profile=browser_profile)
    task.browser_settings.profile.profile_folder_path = browser_profile.profile_dir

    return task


class TestTaskStorage:
    @pytest.fixture(autouse=True)
    def run_around_tests(self) -> Generator[None, None, None]:
        monkeypatch = MonkeyPatch()
        test_dir = tempfile.mkdtemp(prefix="pybas-task-storage-test_")

        assert os.path.exists(test_dir)
        assert os.path.isdir(test_dir)

        monkeypatch.setenv("LOCALAPPDATA", test_dir)
        try:
            yield
        finally:
            monkeypatch.undo()
            if os.path.exists(test_dir):
                shutil.rmtree(test_dir)

    def test_fail_storage_dir(self) -> None:
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
        task_storage = TaskStorage(task_filename=FilePath("custom_tasks.json"))
        assert task_storage.get_all() is None

    def test_failed_custom_task_filename(self, storage_dir: DirectoryPath, profiles_dir: DirectoryPath) -> None:
        with pytest.raises(ValueError):
            TaskStorage(task_filename=FilePath(os.path.join("some_dir", "custom_tasks.json")))

    def tests_default_storage_dir(self, storage_dir: DirectoryPath) -> None:
        os.environ["LOCALAPPDATA"] = str(storage_dir)
        task_storage = TaskStorage()
        assert task_storage.get_all() is None

    def test_read_mode(self, storage_dir: DirectoryPath, profiles_dir: DirectoryPath, fingerprint_str: str) -> None:
        task_storage_read_mode = TaskStorage(storage_dir=storage_dir, mode=TaskStorageModeEnum.READ)
        task_storage_write_mode = TaskStorage(storage_dir=storage_dir, mode=TaskStorageModeEnum.READ_WRITE)

        assert task_storage_read_mode.get_all() is None
        task_storage_read_mode.load_all()

        with pytest.raises(ValueError):
            assert task_storage_read_mode.clear()

        task = create_task(profiles_dir=profiles_dir, fingerprint_str=fingerprint_str)
        assert task is not None

        with pytest.raises(ValueError):
            task_storage_read_mode.save(task=task)

        task_storage_write_mode.save(task=task)
        task_storage_read_mode.load_all()

        assert task_storage_read_mode.get_all() is not None
        assert task_storage_read_mode.count() == 1
        with pytest.raises(ValueError):
            assert task_storage_read_mode.clear()

    def test_saved(self, storage_dir: DirectoryPath, profiles_dir: DirectoryPath, fingerprint_str: str) -> None:
        task_storage_write = TaskStorage(storage_dir=storage_dir, mode=TaskStorageModeEnum.READ_WRITE)
        task = create_task(profiles_dir=profiles_dir, fingerprint_str=fingerprint_str)
        assert task is not None
        task_storage_write.save(task=task)

        task_storage_read = TaskStorage(storage_dir=storage_dir, mode=TaskStorageModeEnum.READ)
        assert task_storage_read.load_all() is True
        assert task_storage_read.get_all() is not None
        assert isinstance(task_storage_read.get_all(), List)

        # check that task is saved in storage
        tasks = task_storage_read.get_all()
        assert task in tasks  # type: ignore
        assert task_storage_read.count() == 1

        new_task = create_task(profiles_dir=profiles_dir, fingerprint_str=fingerprint_str)
        assert new_task is not None

        with pytest.raises(ValueError):
            task_storage_read.save(task=new_task)
        assert task_storage_read.count() == 1

    def test_basic(self, storage_dir: DirectoryPath, profiles_dir: DirectoryPath, fingerprint_str: str) -> None:
        task_storage = TaskStorage(storage_dir=storage_dir, mode=TaskStorageModeEnum.READ_WRITE)
        assert task_storage.get_all() is None
        assert task_storage.count() == 0

        with pytest.raises(ValueError):
            task_storage.save_all()

        assert task_storage.clear() is False  # no tasks to clear
        assert task_storage.load_all() is False  # no tasks to load

        tasks_id = []
        for _ in range(0, 10):
            task = create_task(profiles_dir=profiles_dir, fingerprint_str=fingerprint_str)

            assert task is not None
            assert isinstance(task, BasTask)

            task_storage.save(task=task)
            tasks_id.append(str(task.task_id))

        assert task_storage.save_all() is True

        for one in tasks_id:
            exists_task = task_storage.get(task_id=UUID(one))
            assert exists_task is not None
            assert isinstance(exists_task, BasTask)

        assert task_storage.load_all() is True
        assert task_storage.get_all() is not None
        assert isinstance(task_storage.get_all(), List)
        assert task_storage.get_all() is not None
        assert len(task_storage.get_all()) == 10  # type: ignore
        assert task_storage.count() == 10
        assert task_storage.get(task_id=uuid4()) is False

        assert task_storage.clear() is True
        assert task_storage.count() == 0
        assert task_storage.load_all() is False
        assert task_storage.get(task_id=uuid4()) is False

        task = create_task(profiles_dir=profiles_dir, fingerprint_str=fingerprint_str)
        task_storage.save(task=task)
        with pytest.raises(TaskDuplicateError):
            task_storage.save(task=task)

        print(task_storage)  # repr
