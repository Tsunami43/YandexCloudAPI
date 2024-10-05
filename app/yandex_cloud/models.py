from typing import Dict, Any, Optional

mime_types = {
    "Изображения": [
        "image/jpeg",
        "image/png",
        "image/gif",
        "image/bmp",
        "image/webp",
    ],
    "Документы": [
        "application/pdf",
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/vnd.ms-excel",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ],
    "Видеофайлы": [
        "video/mp4",
        "video/x-msvideo",
        "video/x-flv",
        "video/quicktime",
    ],
    "Аудиофайлы": ["audio/mpeg", "audio/wav", "audio/ogg"],
}


class File:
    """Модель, представляющая собой файл с Яндекс Диска."""

    download_dir: str = "downloads"

    def __init__(
        self,
        public_key: str,
        name: str,
        _type: str,
        path: str,
        download_url: Optional[str],
        mime_type: Optional[str] = None,  # Добавляем mime_type
    ):
        self.public_key = public_key
        self.name = name
        self.type = _type
        self.download_url = download_url
        self.path = path
        self.mime_type = mime_type  # Присваиваем mime_type атрибуту

    @property
    def is_folder(self):
        return self.type == "dir"

    @classmethod
    def from_json(cls, data: Dict[str, Any]) -> "File":
        """Создайте экземпляр файла из словаря, подобного JSON."""
        return cls(
            public_key=data["public_key"],
            name=data["name"],
            _type=data["type"],
            path=data["path"],
            download_url=data.get("file"),
            mime_type=data.get("mime_type"),  # Извлекаем mime_type из данных
        )

    def is_valid_mime_type(self, selected_type: str) -> bool:
        """Проверяет, соответствует ли mime_type выбранному типу."""
        if selected_type == "Все файлы":
            return True
        if selected_type in mime_types:
            return self.mime_type in mime_types[selected_type]
        return False

    def __repr__(self):
        return f"File(public_key={self.public_key}, name={self.name}, type={self.type}, mime_type={self.mime_type}, download_url={self.download_url}, path={self.path})"
