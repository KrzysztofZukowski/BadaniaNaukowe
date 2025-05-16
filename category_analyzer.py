# category_analyzer.py
import os
import re
import json
import traceback
from datetime import datetime
from collections import Counter, defaultdict

# Rozszerzony słownik rozszerzeń do kategorii plików
FILE_CATEGORIES = {
    'dokumenty_tekstowe': ['.txt', '.doc', '.docx', '.rtf', '.odt', '.md'],
    'dokumenty_pdf': ['.pdf'],
    'arkusze_kalkulacyjne': ['.xls', '.xlsx', '.csv', '.ods', '.tsv'],
    'prezentacje': ['.ppt', '.pptx', '.odp', '.key'],
    'obrazy_zdjecia': ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.raw', '.webp'],
    'obrazy_wektorowe': ['.svg', '.eps', '.ai'],
    'audio_muzyka': ['.mp3', '.wav', '.flac', '.aac', '.ogg', '.wma', '.m4a'],
    'audio_podcasty': ['.mp3', '.m4a', '.aac', '.wav'],
    'wideo': ['.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm', '.m4v'],
    'archiwa': ['.zip', '.rar', '.7z', '.tar', '.gz', '.bz2', '.xz', '.iso'],
    'kod_skrypty': ['.py', '.js', '.html', '.css', '.java', '.cpp', '.c', '.h', '.php', '.rb', '.go', '.ts'],
    'bazy_danych': ['.db', '.sqlite', '.sql', '.mdb', '.accdb'],
    'wykonywalne': ['.exe', '.msi', '.bat', '.sh', '.cmd', '.app'],
    'projekty_graficzne': ['.psd', '.ai', '.xd', '.sketch', '.fig'],
    'projekty_inne': ['.blend', '.xcodeproj', '.vcproj', '.sln'],
    'ebooki': ['.epub', '.mobi', '.azw', '.azw3', '.fb2'],
    'czcionki': ['.ttf', '.otf', '.woff', '.woff2', '.eot'],
    'pliki_konfiguracyjne': ['.xml', '.json', '.yaml', '.yml', '.ini', '.conf', '.config', '.toml'],
    'animacje': ['.gif', '.swf', '.apng', '.webp'],
    'pliki_3d': ['.obj', '.stl', '.fbx', '.blend', '.3ds', '.dae'],
    'wirtualizacja': ['.vbox', '.vmdk', '.vdi', '.ova', '.ovf'],
    'konfiguracja_systemu': ['.reg', '.sys', '.dll', '.ini', '.cfg'],
    'pliki_office': ['.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.odt', '.ods', '.odp'],
    'mapy_dane_przestrzenne': ['.shp', '.geojson', '.kml', '.kmz', '.gpx']
}

# Odwrotny słownik dla szybkiego wyszukiwania
EXTENSION_TO_CATEGORY = {}
for category, extensions in FILE_CATEGORIES.items():
    for ext in extensions:
        if ext not in EXTENSION_TO_CATEGORY:  # Zapobiegamy nadpisaniu, jeśli rozszerzenie jest już w słowniku
            EXTENSION_TO_CATEGORY[ext.lower()] = category

# Rozszerzone wzorce nazw plików dla kategoryzacji
NAME_PATTERNS = {
    'faktura': [r'faktura', r'rachunek', r'invoice', r'fv', r'paragon', r'bill', r'payment'],
    'cv_resume': [r'cv', r'resume', r'życiorys', r'curriculum', r'bio'],
    'raport': [r'raport', r'report', r'sprawozdanie', r'zestawienie', r'statystyk[ai]', r'podsumowanie'],
    'backup': [r'backup', r'kopia', r'archiwum', r'\bkopia zapasowa\b', r'\bkopia\b', r'bak'],
    'notatka': [r'notatka', r'note', r'notes', r'uwagi', r'zapiski', r'reminder'],
    'projekt': [r'projekt', r'project', r'^proj_', r'^prj_', r'zadanie', r'task'],
    'dokumentacja': [r'dokumentacja', r'documentation', r'manual', r'instrukcja', r'handbook', r'guide'],
    'konfiguracja': [r'config', r'konfiguracja', r'ustawienia', r'settings', r'prefs', r'preferences'],
    'prezentacja': [r'prezentacja', r'presentation', r'slajdy', r'slides'],
    'umowa': [r'umowa', r'kontrakt', r'contract', r'agreement', r'deal'],
    'oferta': [r'oferta', r'offer', r'proposition', r'propozycja', r'cennik', r'pricing'],
    'ankieta': [r'ankieta', r'survey', r'poll', r'questionnaire', r'badanie'],
    'zdjęcia': [r'zdj[ęe]cie', r'zdj[ęe]cia', r'foto', r'photo', r'img'],
    'muzyka': [r'muzyka', r'music', r'song', r'piosenka', r'utwor', r'track'],
    'wideo': [r'wideo', r'video', r'film', r'movie', r'nagranie', r'recording'],
    'szkic': [r'szkic', r'draft', r'draft_', r'szkic_', r'roboczy', r'temp_'],
    'książka': [r'książka', r'book', r'reading', r'lektura', r'powieść', r'novel'],
    'list': [r'list', r'letter', r'pismo', r'korespondencja', r'correspondence'],
    'prywatne': [r'prywatne', r'private', r'personal', r'osobiste'],
    'praca': [r'praca', r'work', r'job', r'zawodowe', r'professional'],
    'szkoła': [r'szkoła', r'school', r'uczelnia', r'studia', r'zadanie', r'homework'],
    'wydarzenie': [r'wydarzenie', r'event', r'impreza', r'party', r'spotkanie', r'meeting'],
}

# Lista słów ignorowanych w nazwach plików (stopwords)
STOPWORDS = {
    'plik', 'obraz', 'file', 'kopia', 'copy', 'nowy', 'new', 'img', 'image', 'doc', 'document',
    'text', 'tekst', 'dane', 'data', 'folder', 'katalog', 'directory', 'tem', 'temp', 'tymczasowy',
    'temporary', 'download', 'pobrane', 'upload', 'final', 'finalny', 'ostateczny', 'last',
    'pierwszy', 'first', 'test', 'testowy', 'example', 'przykład', 'sample', 'próbka'
}

# Wzorce czasowe do identyfikacji plików związanych z datami
DATE_PATTERNS = {
    'dzienny': [r'\d{4}-\d{2}-\d{2}', r'\d{2}-\d{2}-\d{4}', r'\d{2}\.\d{2}\.\d{4}'],
    'miesięczny': [r'\d{4}-\d{2}', r'\d{2}-\d{4}', r'(sty|lut|mar|kwi|maj|cze|lip|sie|wrz|paź|lis|gru)_\d{4}'],
    'roczny': [r'\b\d{4}\b', r'rok_\d{4}', r'year_\d{4}']
}

# Wzorce identyfikujące pliki związane z konkretnymi przedmiotami w szkole
SUBJECT_PATTERNS = {
    'matematyka': [r'mat', r'math', r'matematyka', r'mathematics', r'algebra', r'geometry', r'geometria'],
    'fizyka': [r'fiz', r'phys', r'fizyka', r'physics'],
    'chemia': [r'chem', r'chemia', r'chemistry'],
    'biologia': [r'bio', r'biologia', r'biology'],
    'historia': [r'hist', r'historia', r'history'],
    'geografia': [r'geo', r'geografia', r'geography'],
    'języki': [r'ang', r'eng', r'język', r'language', r'polish', r'angielski', r'niemiecki', r'hiszpański', r'polski'],
    'informatyka': [r'inf', r'informatyka', r'computer', r'programming', r'programowanie', r'it', r'comp']
}


class CategoryAnalyzer:
    def __init__(self, history_file='transfer_history.json'):
        self.history_file = history_file
        self.transfer_history = self._load_history()

    def _load_history(self):
        """Wczytuje historię przenoszenia plików"""
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    history = json.load(f)

                    # Upewnij się, że wszystkie wymagane klucze istnieją
                    if 'extensions' not in history:
                        history['extensions'] = {}
                    if 'patterns' not in history:
                        history['patterns'] = {}
                    if 'destinations' not in history:
                        history['destinations'] = {}
                    if 'content_types' not in history:
                        history['content_types'] = {}

                    return history
            except Exception as e:
                print(f"Błąd podczas wczytywania historii: {e}")
                return {'extensions': {}, 'patterns': {}, 'destinations': {}, 'content_types': {}}

        # Jeśli plik nie istnieje, zwróć pusty słownik z wszystkimi wymaganymi kluczami
        return {'extensions': {}, 'patterns': {}, 'destinations': {}, 'content_types': {}}

    def save_history(self):
        """Zapisuje historię przenoszenia plików"""
        with open(self.history_file, 'w', encoding='utf-8') as f:
            json.dump(self.transfer_history, f, ensure_ascii=False, indent=2)

    def record_transfer(self, file_info):
        """Zapisuje informację o przeniesieniu pliku do historii"""
        if file_info.status != "Przeniesiono" or not file_info.destination_path:
            return

        extension = file_info.extension.lower()
        destination_dir = os.path.dirname(file_info.destination_path)

        # Zapisujemy informacje o rozszerzeniu
        if extension not in self.transfer_history['extensions']:
            self.transfer_history['extensions'][extension] = {}

        if destination_dir not in self.transfer_history['extensions'][extension]:
            self.transfer_history['extensions'][extension][destination_dir] = 0

        self.transfer_history['extensions'][extension][destination_dir] += 1

        # Zapisujemy informacje o wzorcach w nazwie i kategoriach z nazwy
        # Przechodzimy przez wszystkie kategorie z nazwy (zarówno predefiniowane jak i dynamiczne)
        for category_name in file_info.category_name:
            if category_name not in self.transfer_history['patterns']:
                self.transfer_history['patterns'][category_name] = {}

            if destination_dir not in self.transfer_history['patterns'][category_name]:
                self.transfer_history['patterns'][category_name][destination_dir] = 0

            self.transfer_history['patterns'][category_name][destination_dir] += 1

        # Zapisujemy informacje o typie zawartości (MIME)
        if hasattr(file_info, 'mime_type') and file_info.mime_type and file_info.mime_type != "Nieznany (błąd)":
            # Sprawdź, czy klucz 'content_types' istnieje w słowniku transfer_history
            if 'content_types' not in self.transfer_history:
                self.transfer_history['content_types'] = {}

            if file_info.mime_type not in self.transfer_history['content_types']:
                self.transfer_history['content_types'][file_info.mime_type] = {}

            if destination_dir not in self.transfer_history['content_types'][file_info.mime_type]:
                self.transfer_history['content_types'][file_info.mime_type][destination_dir] = 0

            self.transfer_history['content_types'][file_info.mime_type][destination_dir] += 1

        # Zapisujemy ogólne informacje o folderach docelowych
        if destination_dir not in self.transfer_history['destinations']:
            self.transfer_history['destinations'][destination_dir] = 0

        self.transfer_history['destinations'][destination_dir] += 1

        # Zapisujemy historię
        self.save_history()

    def categorize_file(self, file_path):
        """Kategoryzuje plik na podstawie różnych czynników"""
        file_name = os.path.basename(file_path)
        name, extension = os.path.splitext(file_name)
        extension = extension.lower()
        name_lower = name.lower()  # Konwersja na małe litery dla lepszego dopasowania

        try:
            # Pobranie metadanych pliku
            file_stats = os.stat(file_path)
            file_size = file_stats.st_size
            creation_date = datetime.fromtimestamp(file_stats.st_ctime)
            modification_date = datetime.fromtimestamp(file_stats.st_mtime)
        except:
            file_size = 0
            creation_date = None
            modification_date = None

        # Wstępne wyniki kategoryzacji
        results = {
            'kategoria_rozszerzenia': 'nieznana',
            'kategoria_nazwy': [],
            'kategoria_wielkości': self._categorize_by_size(file_size),
            'kategoria_daty': self._categorize_by_date(name_lower, creation_date, modification_date),
            'kategoria_przedmiotu': [],  # Dla plików związanych ze szkołą/nauką
            'kategoria_czasowa': [],  # Dzienne, miesięczne, roczne
            'sugerowane_lokalizacje': [],
            'wszystkie_kategorie': set()  # Zbiór wszystkich kategorii (do łatwiejszego grupowania)
        }

        # 1. Kategoria na podstawie rozszerzenia
        if extension in EXTENSION_TO_CATEGORY:
            results['kategoria_rozszerzenia'] = EXTENSION_TO_CATEGORY[extension]
            results['wszystkie_kategorie'].add(EXTENSION_TO_CATEGORY[extension])

        # 2. Kategoria na podstawie wzorców w nazwie
        for pattern_name, patterns in NAME_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, name_lower):
                    results['kategoria_nazwy'].append(pattern_name)
                    results['wszystkie_kategorie'].add(pattern_name)
                    break

        # 3. Kategoria na podstawie przedmiotu (dla plików szkolnych/edukacyjnych)
        for subject, patterns in SUBJECT_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, name_lower):
                    results['kategoria_przedmiotu'].append(subject)
                    results['wszystkie_kategorie'].add(f"przedmiot_{subject}")
                    break

        # 4. Kategoria na podstawie wzorców czasowych
        for time_pattern_name, patterns in DATE_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, name_lower):
                    results['kategoria_czasowa'].append(time_pattern_name)
                    results['wszystkie_kategorie'].add(f"czas_{time_pattern_name}")
                    break

        # 5. Dynamiczne kategorie z nazwy pliku
        words_from_name = re.findall(r'[a-zA-ZżółćęśąźńŻÓŁĆĘŚĄŹŃ0-9]{3,}', name_lower)
        for word in words_from_name:
            if word not in STOPWORDS and len(word) >= 3:
                if not any(word in pattern for pattern_list in NAME_PATTERNS.values() for pattern in pattern_list):
                    results['kategoria_nazwy'].append(word)
                    results['wszystkie_kategorie'].add(f"słowo_{word}")

        # 6. Sugerowane lokalizacje na podstawie historii
        suggested_locations = []

        # Na podstawie rozszerzenia
        if extension in self.transfer_history['extensions']:
            ext_locations = sorted(
                self.transfer_history['extensions'][extension].items(),
                key=lambda x: x[1],
                reverse=True
            )
            for loc, count in ext_locations[:3]:  # Top 3 lokalizacje
                suggested_locations.append((loc, f"Na podstawie rozszerzenia {extension}", count))

        # Na podstawie wzorców w nazwie
        for pattern_name in results['kategoria_nazwy']:
            if pattern_name in self.transfer_history['patterns']:
                pattern_locations = sorted(
                    self.transfer_history['patterns'][pattern_name].items(),
                    key=lambda x: x[1],
                    reverse=True
                )
                for loc, count in pattern_locations[:2]:  # Top 2 lokalizacje
                    suggested_locations.append((loc, f"Na podstawie wzorca '{pattern_name}'", count))

        # Jeśli brak sugestii, użyj najczęściej używanych folderów
        if not suggested_locations and self.transfer_history['destinations']:
            general_locations = sorted(
                self.transfer_history['destinations'].items(),
                key=lambda x: x[1],
                reverse=True
            )
            for loc, count in general_locations[:2]:  # Top 2 lokalizacje
                suggested_locations.append((loc, "Często używana lokalizacja", count))

        # Sortuj sugestie według liczby wystąpień
        suggested_locations.sort(key=lambda x: x[2], reverse=True)

        # Usuń duplikaty zachowując kolejność
        unique_locations = []
        seen = set()
        for loc, reason, count in suggested_locations:
            if loc not in seen:
                unique_locations.append((loc, reason, count))
                seen.add(loc)

        results['sugerowane_lokalizacje'] = unique_locations

        # Konwersja zbioru wszystkich kategorii na listę dla łatwiejszego przetwarzania
        results['wszystkie_kategorie'] = list(results['wszystkie_kategorie'])

        return results

    def _categorize_by_size(self, file_size):
        """Kategoryzuje plik na podstawie rozmiaru"""
        try:
            # Ensure we have a clean integer value
            if file_size is None:
                file_size = 0
            elif isinstance(file_size, str):
                clean_size = ''.join(c for c in file_size if c.isdigit() or c == '.')
                file_size = int(float(clean_size)) if clean_size else 0
            else:
                file_size = int(file_size) if file_size else 0

            # Print for verification
            print(f"CATEGORIZING: Size {file_size} bytes")

            # Define size constants clearly
            KB = 1024
            MB = KB * 1024
            GB = MB * 1024

            # Use a clear and explicit categorization logic
            if file_size < 10 * KB:
                category = 'bardzo_mały'
            elif file_size < 500 * KB:
                category = 'mały'
            elif file_size < 5 * MB:
                category = 'średni'
            elif file_size < 50 * MB:
                category = 'duży'
            elif file_size < 500 * MB:
                category = 'bardzo_duży'
            else:
                category = 'ogromny'

            print(f"SIZE CATEGORY RESULT: {category} for {file_size} bytes")
            return category

        except Exception as e:
            print(f"Error in _categorize_by_size: {e}")
            traceback.print_exc()
            return 'nieznany'

    def _categorize_by_date(self, name, creation_date, modification_date):
        """Kategoryzuje plik na podstawie daty utworzenia/modyfikacji"""
        if not creation_date or not modification_date:
            return 'nieznana'

        now = datetime.now()
        age_in_days = (now - modification_date).days

        if age_in_days < 1:
            return 'dzisiaj'
        elif age_in_days < 7:
            return 'ostatni_tydzień'
        elif age_in_days < 30:
            return 'ostatni_miesiąc'
        elif age_in_days < 365:
            return 'ostatni_rok'
        else:
            return 'starszy'

    def get_suggested_destination(self, file_path):
        """Zwraca sugerowaną lokalizację docelową dla pliku"""
        categorization = self.categorize_file(file_path)
        suggestions = categorization['sugerowane_lokalizacje']

        if suggestions:
            return suggestions[0][0]  # Pierwsza sugerowana lokalizacja

        return None

    def group_files_by_category(self, files_info_list):
        """Grupuje pliki według różnych kategorii"""
        # Inicjalizacja słowników dla różnych typów grupowania
        grouped_by_extension_category = defaultdict(list)
        grouped_by_name_category = defaultdict(list)
        grouped_by_size = defaultdict(list)
        grouped_by_age = defaultdict(list)
        grouped_by_subject = defaultdict(list)
        grouped_by_time_pattern = defaultdict(list)

        # Wszystkie grupy (do wyświetlenia sumarycznego)
        all_groups = defaultdict(list)

        for file_info in files_info_list:
            # Pobieranie kategoryzacji na podstawie ścieżki źródłowej
            categorization = self.categorize_file(file_info.source_path)

            # Grupowanie według kategorii rozszerzenia
            ext_category = categorization['kategoria_rozszerzenia']
            grouped_by_extension_category[ext_category].append(file_info)
            all_groups[f"rozszerzenie_{ext_category}"].append(file_info)

            # Grupowanie według kategorii nazwy
            for name_cat in categorization['kategoria_nazwy']:
                grouped_by_name_category[name_cat].append(file_info)
                all_groups[f"nazwa_{name_cat}"].append(file_info)

            # Grupowanie według rozmiaru
            size_category = categorization['kategoria_wielkości']
            grouped_by_size[size_category].append(file_info)
            all_groups[f"rozmiar_{size_category}"].append(file_info)

            # Grupowanie według wieku
            age_category = categorization['kategoria_daty']
            grouped_by_age[age_category].append(file_info)
            all_groups[f"wiek_{age_category}"].append(file_info)

            # Grupowanie według przedmiotu
            for subject in categorization['kategoria_przedmiotu']:
                grouped_by_subject[subject].append(file_info)
                all_groups[f"przedmiot_{subject}"].append(file_info)

            # Grupowanie według wzorca czasowego
            for time_pattern in categorization['kategoria_czasowa']:
                grouped_by_time_pattern[time_pattern].append(file_info)
                all_groups[f"czas_{time_pattern}"].append(file_info)

        # Tworzenie wynikowego słownika
        result = {
            'według_rozszerzenia': grouped_by_extension_category,
            'według_nazwy': grouped_by_name_category,
            'według_rozmiaru': grouped_by_size,
            'według_wieku': grouped_by_age,
            'według_przedmiotu': grouped_by_subject,
            'według_wzorca_czasowego': grouped_by_time_pattern,
            'wszystkie_grupy': all_groups
        }

        return result