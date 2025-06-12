# auto_folder_organizer.py - NAPRAWIONA wersja z uproszczonymi kategoriami
import os
import shutil
import re
from datetime import datetime
from collections import defaultdict, Counter
from tkinter import messagebox
import traceback


class AutoFolderOrganizer:
    """Klasa do automatycznego organizowania plików w hierarchicznej strukturze folderów"""

    def __init__(self, category_analyzer):
        self.category_analyzer = category_analyzer

        # UPROSZCZONE mapowanie kategorii - tylko rozszerzenia
        self.main_folder_mapping = {
            'dokumenty_tekstowe': '📄 Dokumenty',
            'dokumenty_pdf': '📄 Dokumenty',
            'arkusze_kalkulacyjne': '📊 Arkusze i Dane',
            'prezentacje': '📊 Arkusze i Dane',
            'obrazy_zdjecia': '🖼️ Zdjęcia i Obrazy',
            'obrazy_wektorowe': '🎨 Grafika',
            'audio_muzyka': '🎵 Audio',
            'audio_podcasty': '🎵 Audio',
            'wideo': '🎬 Video',
            'archiwa': '📦 Archiwa',
            'kod_skrypty': '💻 Kod i Programy',
            'bazy_danych': '💾 Bazy Danych',
            'wykonywalne': '💻 Kod i Programy',
            'projekty_graficzne': '🎨 Grafika',
            'projekty_inne': '🔧 Projekty',
            'ebooki': '📚 Książki',
            'czcionki': '🔤 Czcionki',
            'pliki_konfiguracyjne': '⚙️ Konfiguracja',
            'animacje': '🎞️ Animacje',
            'pliki_3d': '🎯 Pliki 3D',
            'wirtualizacja': '💿 Wirtualizacja',
            'konfiguracja_systemu': '⚙️ Konfiguracja',
            'pliki_office': '📄 Dokumenty',
            'mapy_dane_przestrzenne': '🗺️ Mapy',
            'nieznana': '❓ Inne'
        }

        # NOWE: Mapowanie dynamicznych kategorii
        self.dynamic_folder_mapping = {
            'backup': 'Kopie Zapasowe',
            'config': 'Konfiguracja',
            'temp': 'Pliki Tymczasowe',
            'test': 'Pliki Testowe'
        }

    def generate_folder_structure(self, base_path, files_info_list, organization_mode="full"):
        """
        Generuje strukturę folderów na podstawie listy plików
        """
        print(f"\n=== GENEROWANIE STRUKTURY FOLDERÓW ===")
        print(f"Tryb organizacji: {organization_mode}")
        print(f"Ścieżka bazowa: {base_path}")
        print(f"Liczba plików: {len(files_info_list)}")

        file_mapping = {}
        folder_stats = defaultdict(int)

        for file_info in files_info_list:
            try:
                # Generuj ścieżkę dla tego pliku
                target_path = self._generate_file_path(base_path, file_info, organization_mode)

                # Dodaj do mapowania
                source_path = file_info.source_path
                file_mapping[source_path] = target_path

                # Aktualizuj statystyki folderów
                folder_path = os.path.dirname(target_path)
                folder_stats[folder_path] += 1

                print(f"  {file_info.name}{file_info.extension} -> {os.path.relpath(target_path, base_path)}")

            except Exception as e:
                print(f"Błąd generowania ścieżki dla {file_info.name}: {e}")
                traceback.print_exc()
                continue

        # Wyświetl statystyki
        print(f"\n=== STATYSTYKI STRUKTURY ===")
        print(f"Wygenerowano mapowanie dla {len(file_mapping)} plików")
        print(f"Liczba unikalnych folderów: {len(folder_stats)}")

        # Pokaż największe foldery
        top_folders = sorted(folder_stats.items(), key=lambda x: x[1], reverse=True)[:10]
        for folder, count in top_folders:
            rel_path = os.path.relpath(folder, base_path)
            print(f"  {rel_path}: {count} plików")

        return file_mapping

    def generate_folder_structure_custom(self, base_path, files_info_list, hierarchy_levels):
        """
        Generuje strukturę folderów na podstawie niestandardowej hierarchii
        """
        print(f"\n=== GENEROWANIE STRUKTURY FOLDERÓW (CUSTOM) ===")
        print(f"Hierarchia: {' -> '.join(hierarchy_levels)}")
        print(f"Ścieżka bazowa: {base_path}")
        print(f"Liczba plików: {len(files_info_list)}")

        file_mapping = {}
        folder_stats = defaultdict(int)

        for file_info in files_info_list:
            try:
                # Generuj ścieżkę dla tego pliku używając custom hierarchii
                target_path = self._generate_file_path_custom(base_path, file_info, hierarchy_levels)

                # Dodaj do mapowania
                source_path = file_info.source_path
                file_mapping[source_path] = target_path

                # Aktualizuj statystyki folderów
                folder_path = os.path.dirname(target_path)
                folder_stats[folder_path] += 1

                print(f"  {file_info.name}{file_info.extension} -> {os.path.relpath(target_path, base_path)}")

            except Exception as e:
                print(f"Błąd generowania ścieżki dla {file_info.name}: {e}")
                traceback.print_exc()
                continue

        # Wyświetl statystyki
        print(f"\n=== STATYSTYKI STRUKTURY ===")
        print(f"Wygenerowano mapowanie dla {len(file_mapping)} plików")
        print(f"Liczba unikalnych folderów: {len(folder_stats)}")

        # Pokaż największe foldery
        top_folders = sorted(folder_stats.items(), key=lambda x: x[1], reverse=True)[:10]
        for folder, count in top_folders:
            rel_path = os.path.relpath(folder, base_path)
            print(f"  {rel_path}: {count} plików")

        return file_mapping

    def _sanitize_folder_name(self, name):
        """Sanityzuje nazwę folderu dla Windows - usuwa niedozwolone znaki"""
        if not name:
            return "Inne"

        # Niedozwolone znaki w Windows: < > : " | ? * /  oraz znaki kontrolne
        forbidden_chars = '<>:"|?*/'

        # Zastąp niedozwolone znaki
        sanitized = name
        for char in forbidden_chars:
            sanitized = sanitized.replace(char, ' ')

        # Usuń podwójne spacje
        while '  ' in sanitized:
            sanitized = sanitized.replace('  ', ' ')

        # Usuń spacje z początku i końca
        sanitized = sanitized.strip()

        # Sprawdź długość (Windows ma limit ~255 znaków, ale bezpieczniej 100)
        if len(sanitized) > 100:
            sanitized = sanitized[:100].strip()

        # Nie może być puste po sanityzacji
        if not sanitized:
            sanitized = "Inne"

        # Nie może kończyć się kropką (Windows)
        if sanitized.endswith('.'):
            sanitized = sanitized.rstrip('.').strip()
            if not sanitized:
                sanitized = "Inne"

        return sanitized

    def _generate_file_path(self, base_path, file_info, organization_mode):
        """Generuje pełną ścieżkę dla pojedynczego pliku - NAPRAWIONA wersja dla Windows"""
        path_components = [base_path]

        if organization_mode == "simple":
            # Tylko typ pliku
            main_folder = self._sanitize_folder_name(self._get_main_folder(file_info))
            path_components.append(main_folder)

        elif organization_mode == "by_date":
            # Typ pliku + data
            main_folder = self._sanitize_folder_name(self._get_main_folder(file_info))
            date_folder = self._sanitize_folder_name(self._get_date_folder(file_info))
            path_components.extend([main_folder, date_folder])

        elif organization_mode == "full":
            # Typ pliku + data + dynamiczna kategoria
            main_folder = self._sanitize_folder_name(self._get_main_folder(file_info))
            date_folder = self._sanitize_folder_name(self._get_date_folder(file_info))
            dynamic_folder = self._get_dynamic_folder(file_info)
            if dynamic_folder:
                dynamic_folder = self._sanitize_folder_name(dynamic_folder)

            path_components.append(main_folder)
            if date_folder:
                path_components.append(date_folder)
            if dynamic_folder:
                path_components.append(dynamic_folder)

        elif organization_mode == "theme_first":
            # Dynamiczna kategoria + typ pliku + data
            dynamic_folder = self._get_dynamic_folder(file_info)
            if dynamic_folder:
                dynamic_folder = self._sanitize_folder_name(dynamic_folder)
            main_folder = self._sanitize_folder_name(self._get_main_folder(file_info))
            date_folder = self._sanitize_folder_name(self._get_date_folder(file_info))

            if dynamic_folder:
                path_components.append(dynamic_folder)
            path_components.append(main_folder)
            if date_folder:
                path_components.append(date_folder)

        # Utwórz ścieżkę folderu - używaj os.path.join dla właściwych separatorów
        folder_path = os.path.join(*path_components)

        # Dodaj nazwę pliku - sanityzuj też nazwę pliku
        safe_filename = self._sanitize_filename(f"{file_info.name}{file_info.extension}")
        file_path = os.path.join(folder_path, safe_filename)

        return file_path

    def _generate_file_path_custom(self, base_path, file_info, hierarchy_levels):
        """Generuje pełną ścieżkę dla pliku używając niestandardowej hierarchii"""
        path_components = [base_path]

        # Przejdź przez każdy poziom hierarchii
        for level in hierarchy_levels:
            folder_name = None

            if level == "type":
                # Typ pliku (dokumenty, obrazy, etc.)
                folder_name = self._get_main_folder(file_info)

            elif level == "extension":
                # Rozszerzenie pliku
                ext = file_info.extension.lower() if file_info.extension else "brak_rozszerzenia"
                folder_name = f"Rozszerzenie {ext}"

            elif level == "date":
                # Data
                folder_name = self._get_date_folder(file_info)

            elif level == "size":
                # Rozmiar
                folder_name = f"Rozmiar {file_info.size_category}"

            elif level == "dynamic":
                # Dynamiczne kategorie
                folder_name = self._get_dynamic_folder(file_info)
                if not folder_name:
                    # Jeśli brak dynamicznej kategorii, pomiń ten poziom
                    continue

            # Dodaj folder do ścieżki (jeśli istnieje)
            if folder_name:
                folder_name = self._sanitize_folder_name(folder_name)
                path_components.append(folder_name)

        # Utwórz ścieżkę folderu
        folder_path = os.path.join(*path_components)

        # Dodaj nazwę pliku
        safe_filename = self._sanitize_filename(f"{file_info.name}{file_info.extension}")
        file_path = os.path.join(folder_path, safe_filename)

        return file_path

    def _sanitize_filename(self, filename):
        """Sanityzuje nazwę pliku dla Windows"""
        if not filename:
            return "plik.txt"

        # Niedozwolone znaki w nazwach plików Windows
        forbidden_chars = '<>:"|?*'

        sanitized = filename
        for char in forbidden_chars:
            sanitized = sanitized.replace(char, '_')

        # Nie może kończyć się spacją ani kropką
        sanitized = sanitized.rstrip(' .')

        # Sprawdź długość
        if len(sanitized) > 200:  # Bezpieczny limit
            name, ext = os.path.splitext(sanitized)
            sanitized = name[:200 - len(ext)] + ext

        return sanitized if sanitized else "plik.txt"

    def _get_main_folder(self, file_info):
        """Zwraca nazwę głównego folderu na podstawie typu pliku"""
        category = file_info.category_extension
        return self.main_folder_mapping.get(category, '❓ Inne')

    def _get_date_folder(self, file_info):
        """Zwraca nazwę folderu daty"""
        try:
            # Spróbuj sparsować datę utworzenia
            if file_info.creation_date and file_info.creation_date != "Nieznany":
                # Format daty: YYYY-MM-DD HH:MM:SS
                date_str = file_info.creation_date.split()[0]  # Weź tylko część z datą
                date_obj = datetime.strptime(date_str, '%Y-%m-%d')

                # Zwróć rok i miesiąc
                return f"{date_obj.year}/{date_obj.strftime('%m - %B')}"

            # Fallback na datę modyfikacji
            elif file_info.modification_date and file_info.modification_date != "Nieznany":
                date_str = file_info.modification_date.split()[0]
                date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                return f"{date_obj.year}/{date_obj.strftime('%m - %B')}"

        except Exception as e:
            print(f"Błąd parsowania daty dla {file_info.name}: {e}")

        # Fallback na kategorię daty z analizatora
        date_category = getattr(file_info, 'date_category', 'nieznana')
        date_mapping = {
            'dzisiaj': 'Najnowsze/Dzisiaj',
            'ostatni_tydzień': 'Najnowsze/Ostatni tydzień',
            'ostatni_miesiąc': 'Najnowsze/Ostatni miesiąc',
            'ostatni_rok': 'Ostatni rok',
            'starszy': 'Starsze pliki',
            'nieznana': 'Data nieznana'
        }

        return date_mapping.get(date_category, 'Data nieznana')

    def _get_dynamic_folder(self, file_info):
        """NOWA: Zwraca nazwę folderu na podstawie dynamicznych kategorii - Windows compatible"""
        # Sprawdź najpierw proste wzorce
        if hasattr(file_info, 'category_name') and file_info.category_name:
            for category in file_info.category_name:
                if category in self.dynamic_folder_mapping:
                    return self.dynamic_folder_mapping[category]

                # Sprawdź dynamiczne kategorie - BEZ DWUKROPKA dla Windows!
                if category.startswith('grupa_'):
                    group_name = category.replace('grupa_', '').title()
                    return f"Grupa {group_name}"  # Usunięto dwukropek
                elif category.startswith('seria_'):
                    series_name = category.replace('seria_', '').title()
                    return f"Seria {series_name}"  # Usunięto dwukropek
                elif category.startswith('temat_'):
                    theme_name = category.replace('temat_', '').title()
                    return f"Temat {theme_name}"  # Usunięto dwukropek
                elif category.startswith('typ_'):
                    type_name = category.replace('typ_', '').title()
                    return f"Typ {type_name}"  # Usunięto dwukropek

        # Sprawdź wzorce czasowe
        if hasattr(file_info, 'time_pattern_categories') and file_info.time_pattern_categories:
            if 'dzienny' in file_info.time_pattern_categories:
                return "Pliki Dzienne"
            elif 'miesięczny' in file_info.time_pattern_categories:
                return "Pliki Miesięczne"
            elif 'roczny' in file_info.time_pattern_categories:
                return "Pliki Roczne"

        return None  # Brak dynamicznej kategorii

    def create_folders_and_move_files(self, file_mapping, dry_run=False, use_existing_structure=True):
        """
        Tworzy foldery i przenosi pliki zgodnie z mapowaniem
        """
        print(f"\n=== {'SYMULACJA' if dry_run else 'WYKONANIE'} PRZENOSZENIA ===")
        print(f"Używanie istniejącej struktury: {'TAK' if use_existing_structure else 'NIE'}")

        results = {
            'success': [],
            'failed': [],
            'folders_created': set(),
            'folders_reused': set(),
            'skipped': []
        }

        # Jeśli włączona jest opcja używania istniejącej struktury, przeanalizuj istniejące foldery
        if use_existing_structure:
            existing_structure = self._analyze_existing_structure(file_mapping)
            print(f"\n📁 ISTNIEJĄCA STRUKTURA:")
            for folder_type, paths in existing_structure.items():
                if paths:
                    print(f"  {folder_type}: {len(paths)} istniejących folderów")
        else:
            existing_structure = {}

        for source_path, target_path in file_mapping.items():
            try:
                # Sprawdź czy plik źródłowy istnieje
                if not os.path.exists(source_path):
                    results['failed'].append({
                        'source': source_path,
                        'target': target_path,
                        'error': 'Plik źródłowy nie istnieje'
                    })
                    continue

                # Dostosuj ścieżkę docelową do istniejącej struktury (jeśli włączone)
                if use_existing_structure:
                    target_path = self._adapt_to_existing_structure(target_path, existing_structure)

                # Utwórz folder docelowy
                target_dir = os.path.dirname(target_path)
                folder_existed = os.path.exists(target_dir)

                if not dry_run:
                    if not folder_existed:
                        os.makedirs(target_dir, exist_ok=True)
                        results['folders_created'].add(target_dir)
                        print(f"  📁 Utworzono nowy folder: {os.path.relpath(target_dir)}")
                    else:
                        results['folders_reused'].add(target_dir)
                        print(f"  ♻️  Użyto istniejącego folderu: {os.path.relpath(target_dir)}")
                else:
                    if not folder_existed:
                        results['folders_created'].add(target_dir)
                        print(f"  📁 [SYMULACJA] Utworzę folder: {os.path.relpath(target_dir)}")
                    else:
                        results['folders_reused'].add(target_dir)
                        print(f"  ♻️  [SYMULACJA] Użyję istniejącego: {os.path.relpath(target_dir)}")

                # Sprawdź czy plik docelowy już istnieje
                if os.path.exists(target_path):
                    # Generuj unikalną nazwę
                    base, ext = os.path.splitext(target_path)
                    counter = 1

                    while os.path.exists(f"{base} ({counter}){ext}"):
                        counter += 1

                    target_path = f"{base} ({counter}){ext}"
                    print(f"  🔄 Zmieniono nazwę na: {os.path.basename(target_path)}")

                # Przenieś plik
                if not dry_run:
                    shutil.move(source_path, target_path)
                    print(f"  ✅ Przeniesiono: {os.path.basename(source_path)} -> {os.path.relpath(target_path)}")
                else:
                    print(
                        f"  ✅ [SYMULACJA] Przeniosę: {os.path.basename(source_path)} -> {os.path.relpath(target_path)}")

                results['success'].append({
                    'source': source_path,
                    'target': target_path,
                    'file_name': os.path.basename(source_path),
                    'folder_reused': folder_existed
                })

            except Exception as e:
                error_msg = f"Błąd przenoszenia {source_path}: {e}"
                print(f"  ❌ BŁĄD: {error_msg}")
                traceback.print_exc()

                results['failed'].append({
                    'source': source_path,
                    'target': target_path,
                    'error': str(e)
                })

        # Podsumowanie
        print(f"\n=== PODSUMOWANIE ===")
        print(f"Pomyślnie przeniesione: {len(results['success'])}")
        print(f"Błędy: {len(results['failed'])}")
        print(f"Nowe foldery: {len(results['folders_created'])}")
        print(f"Ponownie użyte foldery: {len(results['folders_reused'])}")

        return results

    def analyze_folder_structure(self, files_info_list, organization_mode="full"):
        """Analizuje jak będzie wyglądać struktura folderów bez tworzenia"""
        folder_preview = defaultdict(list)

        for file_info in files_info_list:
            # Symuluj ścieżkę
            fake_base = "/example"
            target_path = self._generate_file_path(fake_base, file_info, organization_mode)

            # Wyciągnij ścieżkę względną folderu
            relative_folder = os.path.dirname(os.path.relpath(target_path, fake_base))
            folder_preview[relative_folder].append(file_info.name + file_info.extension)

        return dict(folder_preview)

    def analyze_folder_structure_custom(self, files_info_list, hierarchy_levels):
        """Analizuje jak będzie wyglądać struktura folderów dla niestandardowej hierarchii"""
        folder_preview = defaultdict(list)

        for file_info in files_info_list:
            # Symuluj ścieżkę
            fake_base = "/example"
            target_path = self._generate_file_path_custom(fake_base, file_info, hierarchy_levels)

            # Wyciągnij ścieżkę względną folderu
            relative_folder = os.path.dirname(os.path.relpath(target_path, fake_base))
            folder_preview[relative_folder].append(file_info.name + file_info.extension)

        return dict(folder_preview)

    def _analyze_existing_structure(self, file_mapping):
        """Analizuje istniejącą strukturę folderów w lokalizacji docelowej"""
        existing_structure = {
            'main_folders': {},  # typ_pliku -> lista_istniejących_folderów
            'date_folders': {},  # rok -> lista_miesięcy
            'dynamic_folders': {},  # kategoria_dynamiczna -> lista_folderów
        }

        # Zbierz wszystkie unikalne ścieżki bazowe
        base_paths = set()
        for target_path in file_mapping.values():
            # Znajdź główny folder organizacji (zazwyczaj 2-3 poziomy w górę)
            parts = target_path.split(os.sep)
            if len(parts) >= 3:
                base_path = os.sep.join(parts[:-3])  # usuń ostatnie 3 części ścieżki
                base_paths.add(base_path)

        # Analizuj każdą ścieżkę bazową
        for base_path in base_paths:
            if not os.path.exists(base_path):
                continue

            try:
                # Znajdź główne foldery typu pliku (z ikonami emoji)
                for item in os.listdir(base_path):
                    item_path = os.path.join(base_path, item)
                    if os.path.isdir(item_path):
                        # Sprawdź czy to folder głównego typu (zawiera emoji)
                        if any(emoji in item for emoji in ['📄', '🖼️', '🎵', '🎬', '💻', '📊', '📦', '🎨']):
                            folder_type = item
                            existing_structure['main_folders'][folder_type] = []

                            # Znajdź podfoldery z datami
                            self._scan_date_folders(item_path, existing_structure, folder_type)

                print(f"Znaleziono główne foldery: {list(existing_structure['main_folders'].keys())}")
            except Exception as e:
                print(f"Błąd analizy struktury w {base_path}: {e}")

        return existing_structure

    def _scan_date_folders(self, main_folder_path, existing_structure, folder_type):
        """Skanuje foldery z datami w głównym folderze typu pliku"""
        try:
            for item in os.listdir(main_folder_path):
                item_path = os.path.join(main_folder_path, item)
                if os.path.isdir(item_path):
                    # Sprawdź czy to folder z rokiem (4 cyfry)
                    if item.isdigit() and len(item) == 4:
                        year_folder = item
                        existing_structure['date_folders'][year_folder] = []

                        # Znajdź foldery miesięcy
                        year_path = item_path
                        try:
                            for month_item in os.listdir(year_path):
                                month_path = os.path.join(year_path, month_item)
                                if os.path.isdir(month_path):
                                    # Format: "MM - MonthName"
                                    if " - " in month_item and month_item[:2].isdigit():
                                        existing_structure['date_folders'][year_folder].append(month_item)

                                        # Znajdź foldery dynamiczne w miesiącu
                                        self._scan_dynamic_folders(month_path, existing_structure)
                        except OSError:
                            pass

                    # Sprawdź inne możliwe foldery daty
                    elif item in ['Najnowsze', 'Data nieznana', 'Ostatni rok', 'Starsze pliki']:
                        existing_structure['date_folders'][item] = []
                        self._scan_dynamic_folders(item_path, existing_structure)

        except OSError as e:
            print(f"Błąd skanowania folderów dat w {main_folder_path}: {e}")

    def _scan_dynamic_folders(self, date_folder_path, existing_structure):
        """Skanuje dynamiczne foldery w folderze daty"""
        try:
            for item in os.listdir(date_folder_path):
                item_path = os.path.join(date_folder_path, item)
                if os.path.isdir(item_path):
                    # To jest folder dynamiczny
                    dynamic_name = item
                    if dynamic_name not in existing_structure['dynamic_folders']:
                        existing_structure['dynamic_folders'][dynamic_name] = []
                    existing_structure['dynamic_folders'][dynamic_name].append(item_path)

        except OSError as e:
            print(f"Błąd skanowania folderów dynamicznych w {date_folder_path}: {e}")

    def _adapt_to_existing_structure(self, target_path, existing_structure):
        """Dostosowuje ścieżkę docelową do istniejącej struktury folderów"""
        if not existing_structure:
            return target_path

        path_parts = target_path.split(os.sep)
        adapted_parts = path_parts.copy()

        # Sprawdź czy można dostosować główny folder typu
        for i, part in enumerate(path_parts):
            if any(emoji in part for emoji in ['📄', '🖼️', '🎵', '🎬', '💻', '📊', '📦', '🎨']):
                # Sprawdź czy istnieje podobny folder
                for existing_main in existing_structure['main_folders'].keys():
                    # Dopasowanie na podstawie zawartości (bez ikon może się różnić)
                    if self._folders_are_similar(part, existing_main):
                        adapted_parts[i] = existing_main
                        print(f"  🔄 Dostosowano główny folder: {part} -> {existing_main}")
                        break
                break

        # Sprawdź czy można dostosować folder daty
        for i, part in enumerate(path_parts):
            if part.isdigit() and len(part) == 4:  # Folder roku
                if part in existing_structure['date_folders']:
                    # Rok istnieje, sprawdź miesiąc
                    if i + 1 < len(path_parts):
                        month_part = path_parts[i + 1]
                        existing_months = existing_structure['date_folders'][part]

                        # Znajdź podobny miesiąc
                        for existing_month in existing_months:
                            if month_part in existing_month or existing_month in month_part:
                                adapted_parts[i + 1] = existing_month
                                print(f"  🔄 Dostosowano miesiąc: {month_part} -> {existing_month}")
                                break
                break

        # Sprawdź foldery dynamiczne
        for i, part in enumerate(path_parts):
            if part in existing_structure['dynamic_folders']:
                print(f"  🔄 Znaleziono istniejący folder dynamiczny: {part}")
                # Folder dynamiczny już istnieje, nie trzeba zmieniać
                break
            else:
                # Sprawdź podobne foldery dynamiczne
                for existing_dynamic in existing_structure['dynamic_folders'].keys():
                    if self._folders_are_similar(part, existing_dynamic):
                        adapted_parts[i] = existing_dynamic
                        print(f"  🔄 Dostosowano folder dynamiczny: {part} -> {existing_dynamic}")
                        break

        adapted_path = os.sep.join(adapted_parts)

        if adapted_path != target_path:
            print(f"  📁 Ścieżka dostosowana do istniejącej struktury")

        return adapted_path

    def _folders_are_similar(self, folder1, folder2):
        """Sprawdza czy dwa foldery są podobne (ignoruje ikony emoji)"""
        # Usuń emoji i znaki specjalne
        import re
        clean1 = re.sub(r'[^\w\s]', '', folder1).strip().lower()
        clean2 = re.sub(r'[^\w\s]', '', folder2).strip().lower()

        # Sprawdź podobieństwo
        if clean1 == clean2:
            return True

        # Sprawdź czy jeden zawiera drugi
        if clean1 in clean2 or clean2 in clean1:
            return True

        # Sprawdź podobieństwo słów kluczowych
        keywords1 = set(clean1.split())
        keywords2 = set(clean2.split())

        if keywords1 & keywords2:  # Mają wspólne słowa
            return True

        return False

    def get_organization_modes(self):
        """Zwraca dostępne tryby organizacji z opisami - PRZESTARZAŁE, używaj custom hierarchy"""
        # Ta metoda jest zachowana dla kompatybilności wstecznej
        # Nowy system używa niestandardowych hierarchii
        return {
            "simple": {
                "name": "Prosty",
                "description": "Tylko według typu pliku (Dokumenty, Zdjęcia, itp.)",
                "example": "📄 Dokumenty/dokument.pdf"
            },
            "by_date": {
                "name": "Z datą",
                "description": "Typ pliku + rok i miesiąc",
                "example": "📄 Dokumenty/2024/03 - March/dokument.pdf"
            },
            "full": {
                "name": "Pełny",
                "description": "Typ pliku + data + dynamiczne kategorie",
                "example": "📄 Dokumenty/2024/03 - March/Seria: Umowy/dokument.pdf"
            },
            "theme_first": {
                "name": "Dynamiczne pierwsza",
                "description": "Dynamiczne kategorie + typ pliku + data",
                "example": "Seria: Umowy/📄 Dokumenty/2024/03 - March/dokument.pdf"
            }
        }