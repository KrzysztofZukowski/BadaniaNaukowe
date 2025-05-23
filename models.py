# models.py - Uproszczony model danych
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from pathlib import Path
from datetime import datetime


@dataclass
class FileInfo:
    """Uproszczony model informacji o pliku"""
    name: str
    extension: str
    source_path: str
    destination_path: str = ""
    status: str = "pending"
    size: int = 0
    category: str = "nieznana"
    timestamp: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    # Opcjonalne metadane
    creation_date: str = ""
    modification_date: str = ""
    mime_type: str = ""
    keywords: str = ""

    @property
    def display_size(self) -> str:
        """Formatuje rozmiar pliku"""
        if self.size < 1024:
            return f"{self.size} B"
        elif self.size < 1024 ** 2:
            return f"{self.size / 1024:.1f} KB"
        elif self.size < 1024 ** 3:
            return f"{self.size / (1024 ** 2):.1f} MB"
        else:
            return f"{self.size / (1024 ** 3):.1f} GB"

    @property
    def full_name(self) -> str:
        """Zwraca pełną nazwę z rozszerzeniem"""
        return f"{self.name}{self.extension}"

    @classmethod
    def from_path(cls, file_path: str) -> 'FileInfo':
        """Tworzy FileInfo z ścieżki pliku"""
        path = Path(file_path)

        try:
            size = path.stat().st_size
            ctime = datetime.fromtimestamp(path.stat().st_ctime).strftime("%Y-%m-%d %H:%M:%S")
            mtime = datetime.fromtimestamp(path.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S")
        except:
            size = 0
            ctime = mtime = "Nieznana"

        return cls(
            name=path.stem,
            extension=path.suffix,
            source_path=str(path),
            size=size,
            creation_date=ctime,
            modification_date=mtime
        )


@dataclass
class TransferHistory:
    """Historia transferów plików"""
    extensions: Dict[str, Dict[str, int]] = field(default_factory=dict)
    destinations: Dict[str, int] = field(default_factory=dict)

    def record_transfer(self, file_info: FileInfo):
        """Zapisuje transfer do historii"""
        if file_info.status != "success" or not file_info.destination_path:
            return

        ext = file_info.extension.lower()
        dest = str(Path(file_info.destination_path).parent)

        # Aktualizuj historię rozszerzeń
        if ext not in self.extensions:
            self.extensions[ext] = {}
        if dest not in self.extensions[ext]:
            self.extensions[ext][dest] = 0
        self.extensions[ext][dest] += 1

        # Aktualizuj historię destynacji
        if dest not in self.destinations:
            self.destinations[dest] = 0
        self.destinations[dest] += 1

    def suggest_destination(self, extension: str) -> Optional[str]:
        """Sugeruje destynację na podstawie historii"""
        ext = extension.lower()
        if ext in self.extensions:
            destinations = self.extensions[ext]
            return max(destinations.items(), key=lambda x: x[1])[0]
        return None