"""
Settings for the task module.
"""


from pydantic import DirectoryPath, FilePath

_storage_dir = DirectoryPath("PyBASProfilesTasks")

_task_filename = FilePath("tasks.json")
_filelock_filename = FilePath("tasks.lock")
