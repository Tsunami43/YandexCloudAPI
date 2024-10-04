import os
from aiohttp import ClientSession, ClientError
from typing import Optional, List
from loguru import logger
from .models import File


class YandexCloudAPIClient:
    def __init__(self):
        self.base_url = "https://cloud-api.yandex.net/v1/disk/public/resources"

    async def get_files(self, public_key: str) -> Optional[List[File]]:
        """Retrieve the list of files from a public link."""
        async with ClientSession() as session:
            params = {"public_key": public_key}
            try:
                async with session.get(self.base_url, params=params) as response:
                    response.raise_for_status()
                    data = await response.json()
                    logger.info("Files successfully retrieved.")
                    return [File.from_json(item) for item in data["_embedded"]["items"]]
            except ClientError as e:
                logger.error(f"Network error while retrieving files: {e}")
            except Exception as e:
                logger.error(f"An error occurred: {e}")

            return None

    async def download_file(self, file: File):
        """Download this file using a context manager for session and save it in the specified directory structure."""
        if file.download_url is None:
            raise ValueError("'download_url' is None")

        os.makedirs(file.download_dir, exist_ok=True)  # parent dir for downloads
        file_path = os.path.join(file.download_dir, file.name)

        async with ClientSession() as session:
            try:
                async with session.get(file.download_url) as response:
                    response.raise_for_status()
                    content = await response.read()

                    with open(file_path, "wb") as f:
                        f.write(content)

                    logger.info(
                        f"File '{file.name}' successfully downloaded and saved to {file_path}"
                    )
            except ClientError as e:
                logger.error(f"Network error while downloading file '{file.name}': {e}")
            except Exception as e:
                logger.error(
                    f"An error occurred while downloading file '{file.name}': {e}"
                )
