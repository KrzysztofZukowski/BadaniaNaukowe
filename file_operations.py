# file_operations.py
import os
import shutil
import tkinter as tk
from tkinter import filedialog, messagebox
import time
import stat
from datetime import datetime

from models import FileInfo
from file_analyzer import get_mime_type, get_file_signature, extract_keywords, analyze_headers


def select_files():
    """Funkcja otwierająca okno dialogowe do wyboru plików"""
    root = tk.Tk()
    root.withdraw()  # Ukrycie głównego okna tkinter
    files = filedialog.askopenfilenames(
        title="Wybierz pliki do przeniesienia",
        filetypes=(("Wszystkie pliki", "*.*"),)
    )
    return files if files else []


def select_destination():
    """Funkcja otwierająca okno dialogowe do wyboru folderu docelowego"""
    root = tk.Tk()
    root.withdraw()  # Ukrycie głównego okna tkinter
    folder = filedialog.askdirectory(
        title="Wybierz folder docelowy"
    )
    return folder


def format_datetime(timestamp):
    """Formatuje timestamp na czytelną datę"""
    return datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')


def get_file_attributes(file_path):
    """Pobiera atrybuty pliku i zwraca je jako czytelny string"""
    try:
        file_stats = os.stat(file_path)
        attrs = []

        # Sprawdzenie atrybutów na podstawie flag stat
        mode = file_stats.st_mode
        if stat.S_ISDIR(mode):
            attrs.append("Katalog")
        if stat.S_ISREG(mode):
            attrs.append("Plik regularny")
        if mode & stat.S_IRUSR:
            attrs.append("Odczyt")
        if mode & stat.S_IWUSR:
            attrs.append("Zapis")
        if mode & stat.S_IXUSR:
            attrs.append("Wykonanie")

        # Dodatkowe atrybuty specyficzne dla systemu Windows
        try:
            import win32api
            import win32con
            file_attr = win32api.GetFileAttributes(file_path)
            if file_attr & win32con.FILE_ATTRIBUTE_HIDDEN:
                attrs.append("Ukryty")
            if file_attr & win32con.FILE_ATTRIBUTE_SYSTEM:
                attrs.append("Systemowy")
            if file_attr & win32con.FILE_ATTRIBUTE_ARCHIVE:
                attrs.append("Archiwalny")
            if file_attr & win32con.FILE_ATTRIBUTE_READONLY:
                attrs.append("Tylko do odczytu")
        except ImportError:
            # Obsługa sytuacji, gdy nie ma dostępu do modułu win32api
            pass

        return ", ".join(attrs)
    except Exception as e:
        print(f"Błąd podczas pobierania atrybutów pliku: {e}")
        return "Błąd odczytu atrybutów"


def move_files(files, destination):
    """Funkcja przenosząca wybrane pliki do wskazanego folderu"""
    if not os.path.exists(destination):
        os.makedirs(destination)

    files_info = []

    for file_path in files:
        try:
            # Podstawowe informacje o pliku
            file_name = os.path.basename(file_path)
            name, extension = os.path.splitext(file_name)
            destination_path = os.path.join(destination, file_name)

            # Pobieranie podstawowych metadanych przed przeniesieniem pliku
            file_stats = os.stat(file_path)
            file_size = file_stats.st_size  # rozmiar w bajtach
            creation_date = format_datetime(file_stats.st_ctime)
            modification_date = format_datetime(file_stats.st_mtime)
            attributes = get_file_attributes(file_path)

            # Pobieranie zaawansowanych metadanych
            mime_type = get_mime_type(file_path)
            file_signature = get_file_signature(file_path)
            keywords = extract_keywords(file_path)
            headers_info = analyze_headers(file_path)

            # Sprawdzenie, czy plik już istnieje w folderze docelowym
            if os.path.exists(destination_path):
                response = messagebox.askyesno(
                    "Plik już istnieje",
                    f"Plik {file_name} już istnieje w folderze docelowym. Czy chcesz go zastąpić?"
                )
                if not response:
                    files_info.append(FileInfo(
                        name, extension, file_path, "", "Pominięto",
                        file_size, creation_date, modification_date, attributes,
                        mime_type, file_signature, keywords, headers_info
                    ))
                    continue

            # Przeniesienie pliku
            shutil.move(file_path, destination_path)

            # Dodanie informacji o pliku do listy
            files_info.append(FileInfo(
                name, extension, file_path, destination_path, "Przeniesiono",
                file_size, creation_date, modification_date, attributes,
                mime_type, file_signature, keywords, headers_info
            ))
        except Exception as e:
            # W przypadku błędu, próbujemy zebrać jak najwięcej informacji
            try:
                file_stats = os.stat(file_path)
                file_size = file_stats.st_size
                creation_date = format_datetime(file_stats.st_ctime)
                modification_date = format_datetime(file_stats.st_mtime)
                attributes = get_file_attributes(file_path)

                # Dla zaawansowanych metadanych w przypadku błędu używamy placeholderów
                mime_type = "Nieznany (błąd)"
                file_signature = "Nieznany (błąd)"
                keywords = "Nie udało się przeanalizować"
                headers_info = "Nie udało się przeanalizować"
            except:
                file_size = 0
                creation_date = "Nieznany"
                modification_date = "Nieznany"
                attributes = "Nieznany"
                mime_type = "Nieznany (błąd)"
                file_signature = "Nieznany (błąd)"
                keywords = "Nie udało się przeanalizować"
                headers_info = "Nie udało się przeanalizować"

            files_info.append(FileInfo(
                os.path.splitext(os.path.basename(file_path))[0],
                os.path.splitext(os.path.basename(file_path))[1],
                file_path,
                "",
                f"Błąd: {str(e)}",
                file_size, creation_date, modification_date, attributes,
                mime_type, file_signature, keywords, headers_info
            ))
            print(f"Błąd podczas przenoszenia pliku {file_path}: {e}")

    return files_info