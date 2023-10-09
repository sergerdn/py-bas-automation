"""Browser / Browser Settings."""

from typing import List


def browser_command_line_factory() -> List[str]:
    """Browser defaults command line arguments."""

    return [
        "--disk-cache-size=104857600",  # 100 Mb
        "--disable-gpu-program-cache",
        "--disable-gpu-shader-disk-cache",
        "--disable-features=GpuProcessHighPriorityWin,GpuUseDisplayThreadPriority",
        "--lang=en",
    ]
