"""Task storage module. This module is responsible for storing tasks to disk and loading tasks from disk into memory."""

import json
import os
from enum import Enum
from typing import Set, Union
from uuid import UUID

import filelock
from fastapi.encoders import jsonable_encoder
from pydantic import DirectoryPath, FilePath

from pybas_automation.task.models import BasTask
from pybas_automation.task.settings import _filelock_filename, _storage_dir, _task_filename
from pybas_automation.utils import create_storage_dir_in_app_data, get_logger

logger = get_logger()


class TaskStorageModeEnum(str, Enum):
    """Task storage is used to specify the mode to open the tasks file in."""

    READ = "r"
    READ_WRITE = "rw"


class TaskDuplicateError(Exception):
    """Raised when a task already exists in the storage."""


class TaskStorage:
    """TaskStorage is responsible for storing tasks to disk and loading tasks from disk into memory."""

    storage_dir: DirectoryPath
    mode: TaskStorageModeEnum = TaskStorageModeEnum.READ
    task_file_path: FilePath

    _tasks: Union[list[BasTask], None] = None
    _tasks_unique_id: Set[UUID]
    _lock: filelock.FileLock

    def __init__(
        self,
        storage_dir: Union[None, DirectoryPath] = None,
        task_filename: Union[None, FilePath] = None,
        mode: Union[TaskStorageModeEnum, None] = None,
    ) -> None:
        """
        Initialize TaskStorage. If the storage_dir is not provided, the default storage directory will be used.

        :returns: None

        :param storage_dir: The directory to store the tasks file.
        :param task_filename: The filename of the tasks file.
        :param mode: The mode to open the tasks file in. Defaults to read-only.

        :raises ValueError: If the storage_dir is not a directory. If the mode is not a valid value.
        """

        if storage_dir is None:
            self.storage_dir = create_storage_dir_in_app_data(storage_dir=_storage_dir)
        else:
            if not os.path.isdir(storage_dir):
                raise ValueError(f"storage_dir is not a directory: {storage_dir}")
            self.storage_dir = DirectoryPath(storage_dir)

        if task_filename is None:
            self.task_file_path = FilePath(os.path.join(self.storage_dir, _task_filename))
        else:
            task_filename = FilePath(task_filename)
            if task_filename.parent.__str__() != ".":
                raise ValueError(f"task_filename is not a relative path: {task_filename}")

            self.task_file_path = FilePath(os.path.join(self.storage_dir, task_filename))

        # Set the mode of the task storage
        match mode:
            case None:
                self.mode = TaskStorageModeEnum.READ
            case TaskStorageModeEnum.READ:
                self.mode = TaskStorageModeEnum.READ
            case TaskStorageModeEnum.READ_WRITE:
                self.mode = TaskStorageModeEnum.READ_WRITE
            case _:
                raise ValueError(f"mode is not a valid value: {mode}")

        self._tasks_unique_id = set()
        self._lock = filelock.FileLock(os.path.join(self.storage_dir, _filelock_filename))

        self.load_all()

    def __repr__(self) -> str:
        """Return a string representation of the TaskStorage."""
        return f"<TaskStorage storage_dir={self.storage_dir} task_file_path={self.task_file_path} mode={self.mode}>"

    def clear(self) -> bool:
        """
        Clear all tasks from the storage. This will also delete the tasks file and clear the tasks in memory.

        :return: True if the tasks were cleared, False otherwise.

        :raises ValueError: If the task storage is in read-only mode.
        """
        if self.mode == TaskStorageModeEnum.READ:
            raise ValueError("Cannot clear tasks in read mode.")
        if self._lock is None:
            raise ValueError("Lock is not initialized.")

        with self._lock:
            self._tasks = None
            self._tasks_unique_id = set()
            if os.path.exists(self.task_file_path):
                self.task_file_path.unlink()
                return True

        return False

    def save(self, task: BasTask) -> None:
        """
        Save a task to the storage.

        :return:  None

        :param task: The task to save.

        :raises ValueError: If the task storage is in read-only mode or if the task already exists.
        """

        if self.mode == TaskStorageModeEnum.READ:
            raise ValueError("Cannot store tasks in read mode.")
        if self._lock is None:
            raise ValueError("Lock is not initialized.")

        with self._lock:
            if self._tasks is None:
                self._tasks = []
            if task.task_id in self._tasks_unique_id:
                raise TaskDuplicateError(f"Task with id {task.task_id} already exists.")

            self._tasks.append(task)
            self._tasks_unique_id.add(task.task_id)

            _tasks = jsonable_encoder(self._tasks)

            with self.task_file_path.open(mode="w", encoding="utf-8") as f:
                json.dump(_tasks, f, indent=4)

    def update(self, task: BasTask) -> None:
        if self.mode == TaskStorageModeEnum.READ:
            raise ValueError("Cannot store tasks in read mode.")
        if self._lock is None:
            raise ValueError("Lock is not initialized.")
        if self._tasks is None:
            raise ValueError("No tasks to update.")

        with self._lock:
            if task.task_id not in self._tasks_unique_id:
                raise ValueError(f"Task with id {task.task_id} does not exist.")
            found = False

            for num, t in enumerate(self._tasks):
                if t.task_id == task.task_id:
                    found = True
                    self._tasks[num] = task
                    break
            if not found:
                raise ValueError(f"Task with id {task.task_id} does not exist.")

            _tasks = jsonable_encoder(self._tasks)

            with self.task_file_path.open(mode="w", encoding="utf-8") as f:
                json.dump(_tasks, f, indent=4)

    def save_all(self) -> bool:
        """
        Save all tasks to the storage.

        :return: True if the tasks were saved, False otherwise.

        :raises ValueError: If the task storage is in read-only mode.
        """
        if self.mode == TaskStorageModeEnum.READ:
            raise ValueError("Cannot store tasks in read mode.")

        if self._lock is False:
            raise ValueError("Lock is not initialized.")

        if self._tasks is None:
            raise ValueError("No tasks to save.")

        if self._lock is None:
            raise ValueError("Lock is not initialized.")

        with self._lock:
            with self.task_file_path.open(mode="w", encoding="utf-8") as f:
                json.dump([t.model_dump(mode="json") for t in self._tasks], f, indent=4)

        return True

    def get(self, task_id: UUID) -> Union[BasTask, None]:
        """
        Get a task from the storage.

        :param task_id: The task id to get.

        :return: The task if it exists, False otherwise.
        """
        if self._tasks is None:
            return None

        for task in self._tasks:
            if task.task_id == task_id or str(task.task_id) == task_id:
                return task

        return None

    def get_all(self) -> Union[list[BasTask], None]:
        """
        Get all tasks from the storage.

        :return: A list of tasks if they exist, None otherwise.
        """
        if self._tasks is None:
            return None
        return self._tasks

    def count(self) -> int:
        """
        Get the number of tasks in the storage.

        :return:int The number of tasks in the storage.
        """
        if self._tasks is None:
            return 0
        return len(self._tasks)

    def load_all(self) -> bool:
        """
        Load all tasks from the storage into memory.

        :return: True if the tasks were loaded, False otherwise.

        :raises ValueError: If the task storage is in read-only mode.
        """

        # Check if the task file exists.
        if not os.path.exists(self.task_file_path):
            return False

        # Ensure the lock has been initialized.
        if self._lock is None:
            raise ValueError("Lock is not initialized.")

        with self._lock:  # Acquire the lock.
            with self.task_file_path.open(mode="r", encoding="utf-8") as f:
                tasks_from_file = json.load(f)

            # Clear existing tasks in memory.
            self._tasks = []
            self._tasks_unique_id = set()

            # Populate tasks from the file into memory.
            for task_data in tasks_from_file:
                task = BasTask(**task_data)
                self._tasks.append(task)
                self._tasks_unique_id.add(task.task_id)

        return True
