import asyncio
import shutil


async def clean_dir(dir_name: str) -> None:
    await asyncio.sleep(5)
    for _ in range(0, 5):
        try:
            shutil.rmtree(dir_name)
        except Exception as esc:  # type: ignore
            print(esc)
            await asyncio.sleep(5)
        break

    shutil.rmtree(dir_name, ignore_errors=True)
