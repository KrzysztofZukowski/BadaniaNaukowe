# category_analyzer.py - Uproszczony kategorizator plików
import json
import os
from pathlib import Path
from typing import Dict, Optional
from models import FileInfo, TransferHistory


class CategoryAnalyzer:
    """Uproszczony analizator kategorii plików"""

    # Podstawowe kategorie plików
    CATEGORIES = {
        'dokumenty': ['.pdf', '.doc', '.docx', '.txt', '.rtf', '.odt'],
        'arkusze': ['.xls', '.xlsx', '.csv', '.ods'],
        'prezentacje': ['.ppt', '.pptx', '.odp'],
        'obrazy': ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp'],
        'audio': ['.mp3', '.wav', '.flac', '.aac', '.ogg', '.m4a'],
        'wideo': ['.mp4', '.avi', '.mkv', '.mov', '.wmv', '.webm'],
        'archiwa': ['.zip', '.rar', '.7z', '.tar', '.gz'],
        'kod': ['.py', '.js', '.html', '.css', '.java', '.cpp', '.php'],
        'wykonywalne': ['.exe', '.msi', '.deb', '.app'],
        'fonty': ['.ttf', '.otf', '.woff', '.woff2']
    }

    # Mapowanie rozszerzenia -> kategoria
    _extension_map = {}
    for category, extensions in CATEGORIES.items():
        for ext in extensions:
            _extension_map[ext.lower()] = category

    def __init__(self, history_file: str = 'transfer_history.json'):
        self.history_file = history_file
        self.history = self._load_history()

    def _load_history(self) -> TransferHistory:
        """Wczytuje historię transferów"""
        try:
            if Path(self.history_file).exists():
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return TransferHistory(
                        extensions=data.get('extensions', {}),
                        destinations=data.get('destinations', {})
                    )
        except Exception as e:
            print(f"Błąd wczytywania historii: {e}")

        return TransferHistory()

    def save_history(self):
        """Zapisuje historię do pliku"""
        try:
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'extensions': self.history.extensions,
                    'destinations': self.history.destinations
                }, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Błąd zapisywania historii: {e}")

    def categorize_file(self, file_path: str) -> str:
        """Kategoryzuje plik na podstawie rozszerzenia"""
        extension = Path(file_path).suffix.lower()
        return self._extension_map.get(extension, 'inne')

    def suggest_destination(self, file_path: str) -> Optional[str]:
        """Sugeruje lokalizację docelową na podstawie historii"""
        extension = Path(file_path).suffix.lower()
        return self.history.suggest_destination(extension)

    def record_transfer(self, file_info: FileInfo):
        """Zapisuje informację o transferze"""
        self.history.record_transfer(file_info)
        self.save_history()

    def get_category_stats(self) -> Dict[str, int]:
        """Zwraca statystyki kategorii z historii"""
        stats = {}
        for ext, destinations in self.history.extensions.items():
            category = self._extension_map.get(ext, 'inne')
            total_transfers = sum(destinations.values())
            if category in stats:
                stats[category] += total_transfers
            else:
                stats[category] = total_transfers
        return stats

    def get_popular_destinations(self, limit: int = 5) -> list:
        """Zwraca najpopularniejsze destynacje"""
        sorted_destinations = sorted(
            self.history.destinations.items(),
            key=lambda x: x[1],
            reverse=True
        )
        return sorted_destinations[:limit]