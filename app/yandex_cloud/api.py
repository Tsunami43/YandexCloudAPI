import os
from aiohttp import ClientSession, ClientError
from typing import Optional, List
from loguru import logger
from .models import File


class YandexCloudAPIClient:
    def __init__(self):
        self.base_url = "https://cloud-api.yandex.net/v1/disk/public/resources"

    async def get_files(
        self, public_key: str, path: Optional[str] = None
    ) -> Optional[List[File]]:
        """Retrieve the list of files from a public link."""
        async with ClientSession() as session:
            params = {"public_key": public_key}
            if path:
                params["path"] = path
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

    async def download_file(self, download_url: str) -> bytes:
        async with ClientSession() as session:  # Создаем асинхронную сессию
            try:
                async with session.get(
                    download_url
                ) as response:  # Отправляем GET-запрос на скачивание
                    response.raise_for_status()  # Проверяем статус ответа
                    content = await response.read()  # Читаем содержимое файла
                    logger.info(
                        f"Successfully downloaded '{download_url}'."
                    )  # Логируем успешное скачивание
                    return content  # Возвращаем содержимое файла в памяти
            except ClientError as e:
                logger.error(f"Network error while downloading  '{download_url}': {e}")
            except Exception as e:
                logger.error(
                    f"An error occurred while downloading '{download_url}': {e}"
                )

        return None  # Если произошла ошибка, возвращаем None
