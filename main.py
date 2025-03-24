import argparse
import asyncio
import logging
import platform
from aiopath import AsyncPath
from aiofiles import open as aio_open

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("file_sort.log"), logging.StreamHandler()],
)


async def copy_file(src: AsyncPath, dest_folder: AsyncPath):
    try:
        await dest_folder.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        logging.error(f"Failed to create folder {dest_folder}: {e}")
        return

    dest_path = dest_folder / src.name
    if await dest_path.exists():
        logging.warning(f"File {src} already exists in {dest_folder}, skipping.")
        return

    try:
        async with aio_open(src, "rb") as src_file, aio_open(
            dest_path, "wb"
        ) as dest_file:
            while chunk := await src_file.read(1024):
                await dest_file.write(chunk)
        logging.info(f"File {src} has been copied to {dest_folder}")
    except Exception as e:
        logging.error(f"Error while copying {src}: {e}")


async def read_folder(src_folder: AsyncPath, dest_folder: AsyncPath):
    tasks = []
    async for file_path in src_folder.glob("**/*"):
        if await file_path.is_file():
            file_extension = file_path.suffix[1:].lower() or "unknown"
            target_folder = dest_folder / file_extension
            tasks.append(copy_file(file_path, target_folder))

    await asyncio.gather(*tasks)


async def run(source: str, output: str):
    source_folder = AsyncPath(source)
    output_folder = AsyncPath(output)

    if source_folder == output_folder:
        logging.error(
            "Error: The destination folder must not be the same as the source folder."
        )
        return

    if not await source_folder.exists():
        logging.error(f"Source folder {source_folder} does not exist.")
        return

    if not await output_folder.exists():
        logging.info(f"Creating destination folder {output_folder}")
        await output_folder.mkdir(parents=True)

    logging.info("Starting file sorting...")

    await read_folder(source_folder, output_folder)

    logging.info("Sorting completed!")


async def main():
    parser = argparse.ArgumentParser(
        description="Asynchronous file sorting by extension"
    )
    parser.add_argument(
        "--source", "-s", required=True, type=str, help="Path to the source folder"
    )
    parser.add_argument(
        "--output", "-o", required=True, type=str, help="Path to the destination folder"
    )
    args = parser.parse_args()

    await run(args.source, args.output)


if __name__ == "__main__":
    if platform.system() == "Windows":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
