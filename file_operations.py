# file_operations.py - Uproszczone operacje na plikach
import os
import shutil
import mimetypes
from pathlib import Path
from typing import List
from tkinter import filedialog, messagebox
from models import FileInfo
from category_analyzer import CategoryAnalyzer


class FileOperations:
    """Uproszczona klasa do operacji na plikach"""

    def __init__(self, categorizer: CategoryAnalyzer = None):
        self.categorizer = categorizer or CategoryAnalyzer()

    def select_files(self) -> List[str]:
        """Otwiera dialog wyboru plików"""
        return list(filedialog.askopenfilenames(
            title="Wybierz pliki do przeniesienia",
            filetypes=[("Wszystkie pliki", "*.*")]
        ))

    def select_destination(self) -> str:
        """Otwiera dialog wyboru folderu docelowego"""
        return filedialog.askdirectory(title="Wybierz folder docelowy")

    def get_file_info(self, file_path: str) -> FileInfo:
        """Pobiera podstawowe informacje o pliku"""
        # Stwórz podstawowy FileInfo
        file_info = FileInfo.from_path(file_path)

        # Dodaj kategorię
        file_info.category = self.categorizer.categorize_file(file_path)

        # Dodaj typ MIME (opcjonalnie)
        try:
            mime_type, _ = mimetypes.guess_type(file_path)
            file_info.mime_type = mime_type or "unknown"
        except:
            file_info.mime_type = "unknown"

        return file_info

    def move_file(self, file_info: FileInfo, destination_dir: str) -> FileInfo:
        """Przenosi pojedynczy plik"""
        try:
            # Przygotuj ścieżkę docelową
            dest_path = Path(destination_dir) / file_info.full_name

            # Utwórz katalog docelowy jeśli nie istnieje
            dest_path.parent.mkdir(parents=True, exist_ok=True)

            # Sprawdź czy plik już istnieje
            if dest_path.exists():
                response = messagebox.askyesno(
                    "Plik już istnieje",
                    f"Plik {file_info.full_name} już istnieje. Zastąpić?"
                )
                if not response:
                    file_info.status = "skipped"
                    return file_info

            # Przenieś plik
            shutil.move(file_info.source_path, str(dest_path))

            # Aktualizuj informacje
            file_info.destination_path = str(dest_path)
            file_info.status = "success"

            # Zapisz w historii
            self.categorizer.record_transfer(file_info)

        except PermissionError:
            file_info.status = "error: Brak uprawnień"
        except FileNotFoundError:
            file_info.status = "error: Plik nie znaleziony"
        except Exception as e:
            file_info.status = f"error: {str(e)}"

        return file_info

    def copy_file(self, file_info: FileInfo, destination_dir: str) -> FileInfo:
        """Kopiuje pojedynczy plik (zamiast przenoszenia)"""
        try:
            dest_path = Path(destination_dir) / file_info.full_name
            dest_path.parent.mkdir(parents=True, exist_ok=True)

            if dest_path.exists():
                response = messagebox.askyesno(
                    "Plik już istnieje",
                    f"Plik {file_info.full_name} już istnieje. Zastąpić?"
                )
                if not response:
                    file_info.status = "skipped"
                    return file_info

            shutil.copy2(file_info.source_path, str(dest_path))
            file_info.destination_path = str(dest_path)
            file_info.status = "copied"

        except Exception as e:
            file_info.status = f"error: {str(e)}"

        return file_info

    def move_files(self, file_paths: List[str], destination_dir: str) -> List[FileInfo]:
        """Przenosi wiele plików"""
        results = []

        for file_path in file_paths:
            print(f"Przetwarzanie: {file_path}")

            # Pobierz informacje o pliku
            file_info = self.get_file_info(file_path)

            # Przenieś plik
            file_info = self.move_file(file_info, destination_dir)

            results.append(file_info)

            # Wyświetl status
            if file_info.status == "success":
                print(f"✅ {file_info.full_name}")
            elif file_info.status == "skipped":
                print(f"⏩ {file_info.full_name}")
            else:
                print(f"❌ {file_info.full_name}: {file_info.status}")

        return results

    def copy_files(self, file_paths: List[str], destination_dir: str) -> List[FileInfo]:
        """Kopiuje wiele plików"""
        results = []

        for file_path in file_paths:
            file_info = self.get_file_info(file_path)
            file_info = self.copy_file(file_info, destination_dir)
            results.append(file_info)

        return results

    def get_smart_suggestions(self, file_paths: List[str]) -> dict:
        """Zwraca inteligentne sugestie destynacji"""
        suggestions = {}

        for file_path in file_paths:
            suggested = self.categorizer.suggest_destination(file_path)
            if suggested:
                if suggested not in suggestions:
                    suggestions[suggested] = []
                suggestions[suggested].append(Path(file_path).name)

        return suggestions


# Funkcje pomocnicze dla kompatybilności z oryginalnym kodem
def select_files():
    """Funkcja pomocnicza - wybór plików"""
    file_ops = FileOperations()
    return file_ops.select_files()


def select_destination():
    """Funkcja pomocnicza - wybór destynacji"""
    file_ops = FileOperations()
    return file_ops.select_destination()


def move_files(files: List[str], destination: str):
    """Funkcja pomocnicza - przenoszenie plików"""
    file_ops = FileOperations()
    return file_ops.move_files(files, destination)