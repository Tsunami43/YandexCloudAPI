from typing import Dict, Any, Optional, List


class File:
    """Model representing a file from Yandex Disk."""

    download_dir: str = "downloads"

    def __init__(
        self,
        public_key: str,
        name: str,
        _type: str,
        download_url: Optional[str],
        children: Optional[List["File"]] = None,
    ):
        self.public_key = public_key
        self.name = name
        self.type = _type
        self.download_url = download_url
        self.children = children

    @classmethod
    def from_json(cls, data: Dict[str, Any]) -> "File":
        """Create a File instance from a JSON-like dictionary."""
        children = [
            cls.from_json(item) for item in data.get("_embedded", {}).get("items", [])
        ]
        return cls(
            public_key=data["public_key"],
            name=data["name"],
            _type=data["type"],
            download_url=data.get("file"),
            children=children,
        )

    def __repr__(self):
        return f"File(pulic_key={self.public_key}, name={self.name}, type={self.type}, download_url={self.download_url}, children={self.children})"
