
# models.py
from datetime import datetime
import traceback
import os


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

        # Ustawiamy timestamp na aktualny czas w momencie utworzenia obiektu
        self.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Podstawowe metadane
        # Upewniamy się, że file_size jest liczbą
        try:
            # Drukujemy diagnostykę dla rozmiaru pliku
            print(f"FileInfo otrzymał rozmiar: {file_size} typu {type(file_size)}")

            # Konwersja na int z obsługą różnych typów danych
            if file_size is None:
                self.file_size = 0
            elif isinstance(file_size, (int, float)):
                self.file_size = int(file_size)
            elif isinstance(file_size, str):
                # Usuń znaki, które mogą przeszkadzać w konwersji (np. przecinki)
                cleaned_size = ''.join(c for c in file_size if c.isdigit() or c == '.')
                self.file_size = int(float(cleaned_size)) if cleaned_size else 0
            else:
                # Spróbuj bezpośrednio przekonwertować na int
                try:
                    self.file_size = int(file_size)
                except:
                    self.file_size = 0

            print(f"FileInfo ustawił rozmiar na: {self.file_size} typu {type(self.file_size)}")

            # Upewnij się, że rozmiar nie jest ujemny i nie jest podejrzanie mały dla realnego pliku
            if self.file_size < 0:
                print(f"Wykryto ujemny rozmiar ({self.file_size}), ustawiam na 0")
                self.file_size = 0

            # Dla bezpieczeństwa, jeśli znamy ścieżkę źródłową, spróbuj jeszcze raz pobrać rozmiar
            if self.file_size <= 10 and self.source_path and os.path.exists(self.source_path):
                try:
                    direct_size = os.path.getsize(self.source_path)
                    print(f"Wykryto podejrzanie mały rozmiar. Próba bezpośrednia dała: {direct_size}")
                    if direct_size > self.file_size:
                        print(f"Aktualizuję rozmiar z {self.file_size} na {direct_size}")
                        self.file_size = direct_size
                except Exception as size_error:
                    print(f"Nie udało się pobrać bezpośredniego rozmiaru: {size_error}")

        except Exception as e:
            print(f"Błąd konwersji rozmiaru pliku: {e}. Wartość: {file_size}")
            traceback.print_exc()
            self.file_size = 0

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