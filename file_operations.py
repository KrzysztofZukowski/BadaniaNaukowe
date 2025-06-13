# file_operations.py
import os
import shutil
import tkinter as tk
from tkinter import filedialog, messagebox
import time
import stat
import traceback
from datetime import datetime
from file_size_reader import FileSizeReader
from models import FileInfo
from file_analyzer import get_mime_type, get_file_signature, extract_keywords, analyze_headers

# Próbujemy zaimportować rozszerzony analizator, jeśli nie ma - używamy podstawowego
try:
    from enhanced_category_analyzer import EnhancedCategoryAnalyzer
    category_analyzer = EnhancedCategoryAnalyzer()
    print("✅ Używam rozszerzonego analizatora kategorii z inteligentnym grupowaniem")
except ImportError:
    print("⚠️ Nie mogę zaimportować rozszerzonego analizatora, używam podstawowego")
    from category_analyzer import CategoryAnalyzer
    category_analyzer = CategoryAnalyzer()


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
    try:
        # Upewnij się, że timestamp jest liczbą
        timestamp = float(timestamp)
        return datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
    except (ValueError, TypeError, OverflowError) as e:
        print(f"Błąd formatowania daty: {e}, wartość: {timestamp}")
        return "Data nieznana"


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

            # Szczegółowa diagnostyka
            print(f"\n=== Przetwarzanie pliku: {file_path} ===")
            print(f"Nazwa: {name}, Rozszerzenie: {extension}")

            # Sprawdzamy, czy plik istnieje przed próbą pobrania statystyk
            if not os.path.exists(file_path):
                print(f"BŁĄD: Plik {file_path} nie istnieje.")
                continue

            # Pobranie rozmiaru pliku i innych statystyk
            try:
                # Pobranie rozmiaru pliku używając nowej klasy
                file_size = FileSizeReader.get_file_size(file_path)
                formatted_size = FileSizeReader.format_size(file_size)
                print(f"Pobrany rozmiar: {file_size} bajtów ({formatted_size})")

                # Jeśli FileSizeReader zwróci 0 lub niewielki rozmiar, spróbuj jeszcze raz bezpośrednio
                if file_size <= 10 and os.path.exists(file_path):
                    try:
                        direct_size = os.path.getsize(file_path)
                        print(f"Korekta rozmiaru: {direct_size} bajtów zamiast {file_size}")
                        if direct_size > file_size:
                            file_size = direct_size
                            formatted_size = FileSizeReader.format_size(file_size)
                    except Exception as size_err:
                        print(f"Dodatkowa próba odczytu rozmiaru nie powiodła się: {size_err}")

                # Pobieranie dat
                file_stats = os.stat(file_path)
                creation_date = format_datetime(file_stats.st_ctime)
                modification_date = format_datetime(file_stats.st_mtime)

                print(f"Data utworzenia: {creation_date}")
                print(f"Data modyfikacji: {modification_date}")

                attributes = get_file_attributes(file_path)
                print(f"Atrybuty: {attributes}")
            except Exception as stats_error:
                print(f"BŁĄD podczas odczytu statystyk pliku: {stats_error}")
                traceback.print_exc()

                # Ponowna próba uzyskania rozmiaru
                try:
                    file_size = os.path.getsize(file_path)
                    print(f"Powtórna próba odczytu rozmiaru: {file_size} bajtów")
                except:
                    file_size = 0
                    print("Nie udało się odczytać rozmiaru pliku!")

                creation_date = "Nieznany"
                modification_date = "Nieznany"
                attributes = "Błąd odczytu atrybutów"

            # Pobieranie zaawansowanych metadanych
            mime_type = get_mime_type(file_path)
            file_signature = get_file_signature(file_path)
            keywords = extract_keywords(file_path)
            headers_info = analyze_headers(file_path)

            print(f"MIME: {mime_type}")
            print(f"Sygnatura: {file_signature}")

            # Kategoryzacja pliku
            print(f"Uruchamiam kategoryzację...")
            categorization = category_analyzer.categorize_file(file_path)

            # Podstawowe kategorie
            category_extension = categorization['kategoria_rozszerzenia']
            category_name = categorization['kategoria_nazwy']
            suggested_locations = categorization['sugerowane_lokalizacje']

            # Nowe kategorie
            size_category = categorization['kategoria_wielkości']
            date_category = categorization['kategoria_daty']
            subject_categories = categorization.get('kategoria_przedmiotu', [])
            time_pattern_categories = categorization.get('kategoria_czasowa', [])
            all_categories = categorization.get('wszystkie_kategorie', [])

            print(f"Kategoria rozszerzenia: {category_extension}")
            print(f"Kategorie z nazwy: {category_name}")
            print(f"Kategoria rozmiaru: {size_category}")
            print(f"Kategoria daty: {date_category}")
            print(f"Kategorie przedmiotów: {subject_categories}")
            print(f"Kategorie czasowe: {time_pattern_categories}")
            print(f"Wszystkie kategorie: {len(all_categories)} elementów")

            # Sprawdzenie, czy plik już istnieje w folderze docelowym
            if os.path.exists(destination_path):
                response = messagebox.askyesno(
                    "Plik już istnieje",
                    f"Plik {file_name} już istnieje w folderze docelowym. Czy chcesz go zastąpić?"
                )
                if not response:
                    print(f"Pomijanie pliku (już istnieje): {file_name}")
                    file_info_skip = FileInfo(
                        name, extension, file_path, "", "Pominięto",
                        file_size, creation_date, modification_date, attributes,
                        mime_type, file_signature, keywords, headers_info,
                        category_extension, category_name, suggested_locations,
                        size_category, date_category, subject_categories,
                        time_pattern_categories, all_categories
                    )
                    files_info.append(file_info_skip)
                    continue

            # Przeniesienie pliku
            print(f"Przenoszenie pliku z {file_path} do {destination_path}")
            shutil.move(file_path, destination_path)
            print(f"Plik pomyślnie przeniesiony")

            # Aktualny czas przeniesienia
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"Czas operacji: {current_time}")

            # Tworzenie obiektu FileInfo
            print("\n=== Dane przekazywane do FileInfo ===")
            print(f"name: {name}, extension: {extension}")
            print(f"source_path: {file_path}, destination_path: {destination_path}")
            print(f"status: Przeniesiono, file_size: {file_size} typu {type(file_size)}")
            print(f"creation_date: {creation_date}, modification_date: {modification_date}")
            print(f"timestamp będzie ustawiony na: {current_time}")

            # Utworzenie obiektu z informacjami o pliku
            file_info = FileInfo(
                name, extension, file_path, destination_path, "Przeniesiono",
                file_size, creation_date, modification_date, attributes,
                mime_type, file_signature, keywords, headers_info,
                category_extension, category_name, suggested_locations,
                size_category, date_category, subject_categories,
                time_pattern_categories, all_categories
            )

            # Ustawienie czasu operacji (timestamp) na aktualny czas
            file_info.timestamp = current_time
            print(f"DEBUG: Final size category for {file_name}: {file_info.size_category}")

            # Sprawdźmy, czy file_size został poprawnie zapisany w obiekcie
            print(f"Zapisany w FileInfo rozmiar: {file_info.file_size} typu {type(file_info.file_size)}")

            # Zapisanie informacji o przeniesieniu w historii
            category_analyzer.record_transfer(file_info)

            # Dodanie informacji o pliku do listy
            files_info.append(file_info)
            print(f"Dodano informację o pliku do listy wyników")

        except Exception as e:
            # W przypadku błędu, próbujemy zebrać jak najwięcej informacji
            error_message = f"Błąd podczas przenoszenia pliku {file_path}: {e}"
            print(f"\n=== BŁĄD ===\n{error_message}")
            traceback.print_exc()

            try:
                # Próba odczytu rozmiaru pliku nawet w przypadku błędu
                file_size = 0
                if os.path.exists(file_path):
                    try:
                        file_size = FileSizeReader.get_file_size(file_path)
                    except Exception as size_error:
                        try:
                            file_size = os.path.getsize(file_path)
                        except:
                            file_size = 0
                    print(f"Rozmiar pliku w obsłudze błędu: {file_size} bajtów")

                    print(f"Próba odczytu danych pliku podczas obsługi błędu...")
                    file_stats = os.stat(file_path)
                    creation_date = format_datetime(file_stats.st_ctime)
                    modification_date = format_datetime(file_stats.st_mtime)
                    attributes = get_file_attributes(file_path)
                else:
                    print(f"Plik {file_path} nie istnieje podczas obsługi błędu.")
                    creation_date = "Nieznany"
                    modification_date = "Nieznany"
                    attributes = "Nieznany"

                # Dla zaawansowanych metadanych w przypadku błędu używamy placeholderów
                mime_type = "Nieznany (błąd)"
                file_signature = "Nieznany (błąd)"
                keywords = "Nie udało się przeanalizować"
                headers_info = "Nie udało się przeanalizować"

                # Próbujemy uzyskać informacje o kategoryzacji nawet w przypadku błędu
                try:
                    categorization = category_analyzer.categorize_file(file_path)
                    category_extension = categorization['kategoria_rozszerzenia']
                    category_name = categorization['kategoria_nazwy']
                    suggested_locations = categorization['sugerowane_lokalizacje']
                    size_category = categorization['kategoria_wielkości']
                    date_category = categorization['kategoria_daty']
                    subject_categories = categorization.get('kategoria_przedmiotu', [])
                    time_pattern_categories = categorization.get('kategoria_czasowa', [])
                    all_categories = categorization.get('wszystkie_kategorie', [])
                except Exception as cat_error:
                    print(f"Błąd kategoryzacji: {cat_error}")
                    category_extension = "Nieznana"
                    category_name = []
                    suggested_locations = []
                    size_category = "Nieznana"
                    date_category = "Nieznana"
                    subject_categories = []
                    time_pattern_categories = []
                    all_categories = []

            except Exception as inner_error:
                print(f"Błąd podczas zbierania informacji o pliku: {inner_error}")
                traceback.print_exc()
                file_size = 0
                creation_date = "Nieznany"
                modification_date = "Nieznany"
                attributes = "Nieznany"
                mime_type = "Nieznany (błąd)"
                file_signature = "Nieznany (błąd)"
                keywords = "Nie udało się przeanalizować"
                headers_info = "Nie udało się przeanalizować"
                category_extension = "Nieznana"
                category_name = []
                suggested_locations = []
                size_category = "Nieznana"
                date_category = "Nieznana"
                subject_categories = []
                time_pattern_categories = []
                all_categories = []

            # Aktualny czas błędu
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            print(f"Tworzenie obiektu FileInfo dla błędu, rozmiar: {file_size} typu {type(file_size)}")

            error_file_info = FileInfo(
                os.path.splitext(os.path.basename(file_path))[0],
                os.path.splitext(os.path.basename(file_path))[1],
                file_path,
                "",
                f"Błąd: {str(e)}",
                file_size, creation_date, modification_date, attributes,
                mime_type, file_signature, keywords, headers_info,
                category_extension, category_name, suggested_locations,
                size_category, date_category, subject_categories,
                time_pattern_categories, all_categories
            )

            # Ustawienie czasu operacji (timestamp) na aktualny czas
            error_file_info.timestamp = current_time

            # Sprawdźmy, czy file_size został poprawnie zapisany w obiekcie błędu
            print(f"Zapisany w FileInfo (błąd) rozmiar: {error_file_info.file_size} typu {type(error_file_info.file_size)}")

            files_info.append(error_file_info)
            print(f"Dodano informację o błędzie pliku do listy wyników")

    print(f"\n=== Podsumowanie operacji ===")
    print(f"Przetworzono plików: {len(files_info)}")
    for idx, fi in enumerate(files_info):
        formatted_size = FileSizeReader.format_size(fi.file_size)
        print(f"{idx + 1}. {fi.name}{fi.extension}: rozmiar={fi.file_size} ({formatted_size}), status={fi.status}")

    # Dodatkowe: Pokaż podgląd inteligentnego grupowania (jeśli dostępne)
    if len(files_info) > 1 and hasattr(category_analyzer, 'smart_group_files_by_name'):
        print(f"\n🧠 === PODGLĄD INTELIGENTNEGO GRUPOWANIA ===")
        try:
            smart_groups = category_analyzer.smart_group_files_by_name(files_info)
            print(f"Znaleziono {len(smart_groups)} inteligentnych grup:")
            for group_name, group_files in smart_groups.items():
                print(f"  📁 {group_name}: {len(group_files)} plików")
        except Exception as group_error:
            print(f"Nie udało się wygenerować podglądu grupowania: {group_error}")

    return files_info