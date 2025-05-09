# models.py
from datetime import datetime


class FileInfo:
    """Klasa przechowująca informacje o przeniesionym pliku"""

    def __init__(self, name, extension, source_path, destination_path, status,
                 file_size=0, creation_date="", modification_date="", attributes="",
                 mime_type="", file_signature="", keywords="", headers_info="",
                 category_extension="", category_name=None, suggested_locations=None,
                 size_category="", date_category="", subject_categories=None,
                 time_pattern_categories=None, all_categories=None):
        self.name = name
        self.extension = extension
        self.source_path = source_path
        self.destination_path = destination_path
        self.status = status
        self.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Podstawowe metadane
        self.file_size = file_size  # rozmiar w bajtach
        self.creation_date = creation_date
        self.modification_date = modification_date
        self.attributes = attributes  # atrybuty pliku jako string

        # Zaawansowane metadane
        self.mime_type = mime_type
        self.file_signature = file_signature
        self.keywords = keywords
        self.headers_info = headers_info

        # Informacje o kategoryzacji
        self.category_extension = category_extension  # kategoria na podstawie rozszerzenia
        self.category_name = category_name or []  # kategorie na podstawie nazwy
        self.suggested_locations = suggested_locations or []  # sugerowane lokalizacje

        # Nowe kategorie
        self.size_category = size_category  # kategoria według rozmiaru
        self.date_category = date_category  # kategoria według daty
        self.subject_categories = subject_categories or []  # kategorie przedmiotów
        self.time_pattern_categories = time_pattern_categories or []  # kategorie wzorców czasowych
        self.all_categories = all_categories or []  # wszystkie kategorie razem