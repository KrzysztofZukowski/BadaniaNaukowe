# category_analyzer.py - UPROSZCZONA wersja z dynamicznymi kategoriami
import os
import re
import json
import traceback
from datetime import datetime
from collections import Counter, defaultdict

# Zostaw TYLKO rozszerzenia - reszta będzie dynamiczna
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

# Odwrotny słownik dla rozszerzeń
EXTENSION_TO_CATEGORY = {}
for category, extensions in FILE_CATEGORIES.items():
    for ext in extensions:
        if ext not in EXTENSION_TO_CATEGORY:
            EXTENSION_TO_CATEGORY[ext.lower()] = category

# USUŃ wszystkie predefiniowane wzorce - będziemy używać tylko dynamicznych!
# Zostaw tylko kilka oczywistych wzorców które naprawdę działają
SIMPLE_PATTERNS = {
    'backup': [r'\bbackup\b', r'\bkopia\b', r'\bbak\b'],
    'config': [r'\bconfig\b', r'\bkonfig\b', r'\bustawienia\b', r'\bsettings\b'],
    'temp': [r'\btemp\b', r'\btmp\b', r'\btymczasowy\b'],
    'test': [r'\btest\b', r'\btestowy\b', r'\bproba\b']
}

# Słowa do ignorowania w dynamicznych kategoriach
IGNORE_WORDS = {
    'plik', 'file', 'dokument', 'document', 'obraz', 'image', 'foto', 'photo',
    'nowy', 'new', 'stary', 'old', 'kopia', 'copy', 'final', 'ostateczny',
    'wersja', 'version', 'draft', 'szkic', 'temp', 'tymczasowy', 'test',
    'bez', 'tytulu', 'untitled', 'bez_nazwy', 'unnamed', 'noname'
}


class CategoryAnalyzer:
    def __init__(self, history_file='transfer_history.json'):
        self.history_file = history_file
        self.transfer_history = self._load_history()
        # Nowa: historia dynamicznych kategorii
        self.dynamic_patterns = defaultdict(int)  # wzorzec -> liczba wystąpień
        self._load_dynamic_patterns()

    def _load_history(self):
        """Wczytuje historię przenoszenia plików"""
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    history = json.load(f)

                    required_keys = ['extensions', 'patterns', 'destinations', 'content_types']
                    for key in required_keys:
                        if key not in history:
                            history[key] = {}
                    return history
            except Exception as e:
                print(f"Błąd podczas wczytywania historii: {e}")

        return {'extensions': {}, 'patterns': {}, 'destinations': {}, 'content_types': {}}

    def _load_dynamic_patterns(self):
        """Wczytuje dynamiczne wzorce z historii"""
        try:
            dynamic_file = 'dynamic_patterns.json'
            if os.path.exists(dynamic_file):
                with open(dynamic_file, 'r', encoding='utf-8') as f:
                    self.dynamic_patterns = defaultdict(int, json.load(f))
        except Exception as e:
            print(f"Błąd wczytywania dynamicznych wzorców: {e}")

    def _save_dynamic_patterns(self):
        """Zapisuje dynamiczne wzorce"""
        try:
            with open('dynamic_patterns.json', 'w', encoding='utf-8') as f:
                json.dump(dict(self.dynamic_patterns), f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Błąd zapisywania dynamicznych wzorców: {e}")

    def save_history(self):
        """Zapisuje historię przenoszenia plików"""
        with open(self.history_file, 'w', encoding='utf-8') as f:
            json.dump(self.transfer_history, f, ensure_ascii=False, indent=2)

    def categorize_file(self, file_path):
        """UPROSZCZONA kategoryzacja - tylko rozszerzenia + dynamiczne kategorie"""
        file_name = os.path.basename(file_path)
        name, extension = os.path.splitext(file_name)
        extension = extension.lower()
        name_lower = name.lower()

        try:
            file_stats = os.stat(file_path)
            file_size = file_stats.st_size
            creation_date = datetime.fromtimestamp(file_stats.st_ctime)
            modification_date = datetime.fromtimestamp(file_stats.st_mtime)
        except:
            file_size = 0
            creation_date = None
            modification_date = None

        results = {
            'kategoria_rozszerzenia': 'nieznana',
            'kategoria_nazwy': [],
            'kategoria_wielkości': self._categorize_by_size(file_size),
            'kategoria_daty': self._categorize_by_date(name_lower, creation_date, modification_date),
            'kategoria_przedmiotu': [],
            'kategoria_czasowa': [],
            'sugerowane_lokalizacje': [],
            'wszystkie_kategorie': set()
        }

        # 1. Kategoria na podstawie rozszerzenia (jedyna predefiniowana)
        if extension in EXTENSION_TO_CATEGORY:
            results['kategoria_rozszerzenia'] = EXTENSION_TO_CATEGORY[extension]
            results['wszystkie_kategorie'].add(EXTENSION_TO_CATEGORY[extension])

        # 2. Sprawdź tylko kilka prostych wzorców
        for pattern_name, patterns in SIMPLE_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, name_lower):
                    results['kategoria_nazwy'].append(pattern_name)
                    results['wszystkie_kategorie'].add(pattern_name)
                    break

        # 3. NOWE: Dynamiczne kategorie z nazwy pliku
        dynamic_categories = self._extract_dynamic_categories(name_lower)
        results['kategoria_nazwy'].extend(dynamic_categories)
        for cat in dynamic_categories:
            results['wszystkie_kategorie'].add(cat)

        # 4. Wzorce czasowe
        time_patterns = self._detect_time_patterns(name_lower)
        results['kategoria_czasowa'] = time_patterns
        for pattern in time_patterns:
            results['wszystkie_kategorie'].add(f"czas_{pattern}")

        # 5. Kategorie wielkości i daty
        results['wszystkie_kategorie'].add(f"rozmiar_{results['kategoria_wielkości']}")
        results['wszystkie_kategorie'].add(f"data_{results['kategoria_daty']}")

        # 6. Sugerowane lokalizacje z historii
        results['sugerowane_lokalizacje'] = self._get_suggested_locations(
            extension, results['kategoria_nazwy']
        )

        results['wszystkie_kategorie'] = list(results['wszystkie_kategorie'])

        # Zapisz nowe dynamiczne wzorce
        self._learn_from_filename(name_lower)

        return results

    def _extract_dynamic_categories(self, filename):
        """NOWA: Ekstraktuje dynamiczne kategorie z nazwy pliku"""
        categories = []

        # Usuń cyfry i znaki specjalne, zostaw tylko słowa
        clean_name = re.sub(r'[^\w\s]', ' ', filename)
        clean_name = re.sub(r'\d+', ' ', clean_name)

        # Podziel na słowa
        words = [w.strip() for w in clean_name.split() if len(w.strip()) >= 3]

        # Filtruj słowa ignorowane
        meaningful_words = [w for w in words if w not in IGNORE_WORDS]

        # Znajdź najbardziej znaczące słowa (najdłuższe lub z historii)
        for word in meaningful_words:
            if len(word) >= 4:  # Minimum 4 znaki
                # Sprawdź czy to słowo już wystąpiło w historii
                if word in self.dynamic_patterns and self.dynamic_patterns[word] >= 2:
                    categories.append(f"grupa_{word}")
                elif len(word) >= 6:  # Długie słowa są prawdopodobnie znaczące
                    categories.append(f"temat_{word}")

        # Znajdź prefiksy i sufiksy (pierwsze/ostatnie słowo)
        if meaningful_words:
            first_word = meaningful_words[0]
            if len(first_word) >= 4:
                categories.append(f"seria_{first_word}")

            if len(meaningful_words) > 1:
                last_word = meaningful_words[-1]
                if len(last_word) >= 4 and last_word != first_word:
                    categories.append(f"typ_{last_word}")

        return categories[:3]  # Maksymalnie 3 kategorie dynamiczne

    def _learn_from_filename(self, filename):
        """Uczy się z nazw plików dla przyszłych kategoryzacji"""
        # Ekstraktuj słowa kluczowe
        words = re.findall(r'[a-zA-ZżółćęśąźńŻÓŁĆĘŚĄŹŃ]{4,}', filename)

        for word in words:
            if word not in IGNORE_WORDS:
                self.dynamic_patterns[word] += 1

        # Zapisuj co 10 nowych wzorców
        if sum(self.dynamic_patterns.values()) % 10 == 0:
            self._save_dynamic_patterns()

    def _detect_time_patterns(self, name):
        """Wykrywa wzorce czasowe w nazwie pliku"""
        patterns = []

        # Proste wzorce dat
        if re.search(r'\d{4}-\d{2}-\d{2}', name):
            patterns.append('dzienny')
        elif re.search(r'\d{4}-\d{2}', name):
            patterns.append('miesięczny')
        elif re.search(r'\b\d{4}\b', name):
            patterns.append('roczny')

        return patterns

    def _categorize_by_size(self, file_size):
        """Kategoryzuje plik na podstawie rozmiaru"""
        try:
            file_size = int(file_size) if file_size else 0

            KB = 1024
            MB = KB * 1024
            GB = MB * 1024

            if file_size < 10 * KB:
                return 'bardzo_mały'
            elif file_size < 500 * KB:
                return 'mały'
            elif file_size < 5 * MB:
                return 'średni'
            elif file_size < 50 * MB:
                return 'duży'
            elif file_size < 500 * MB:
                return 'bardzo_duży'
            else:
                return 'ogromny'
        except:
            return 'nieznany'

    def _categorize_by_date(self, name, creation_date, modification_date):
        """Kategoryzuje plik na podstawie daty"""
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

    def _get_suggested_locations(self, extension, name_categories):
        """Pobiera sugerowane lokalizacje na podstawie historii"""
        suggestions = []

        # Na podstawie rozszerzenia
        if extension in self.transfer_history['extensions']:
            ext_locations = sorted(
                self.transfer_history['extensions'][extension].items(),
                key=lambda x: x[1], reverse=True
            )
            for loc, count in ext_locations[:2]:
                suggestions.append((loc, f"Rozszerzenie {extension}", count))

        # Na podstawie kategorii nazwy
        for category in name_categories:
            if category in self.transfer_history['patterns']:
                pattern_locations = sorted(
                    self.transfer_history['patterns'][category].items(),
                    key=lambda x: x[1], reverse=True
                )
                for loc, count in pattern_locations[:1]:
                    suggestions.append((loc, f"Kategoria '{category}'", count))

        return suggestions

    def record_transfer(self, file_info):
        """Zapisuje informację o przeniesieniu pliku do historii"""
        if file_info.status != "Przeniesiono" or not file_info.destination_path:
            return

        extension = file_info.extension.lower()
        destination_dir = os.path.dirname(file_info.destination_path)

        # Zapisz historię rozszerzeń
        if extension not in self.transfer_history['extensions']:
            self.transfer_history['extensions'][extension] = {}
        if destination_dir not in self.transfer_history['extensions'][extension]:
            self.transfer_history['extensions'][extension][destination_dir] = 0
        self.transfer_history['extensions'][extension][destination_dir] += 1

        # Zapisz historię wzorców
        for category_name in file_info.category_name:
            if category_name not in self.transfer_history['patterns']:
                self.transfer_history['patterns'][category_name] = {}
            if destination_dir not in self.transfer_history['patterns'][category_name]:
                self.transfer_history['patterns'][category_name][destination_dir] = 0
            self.transfer_history['patterns'][category_name][destination_dir] += 1

        # Zapisz historię
        self.save_history()

    def group_files_by_category(self, files_info_list):
        """Grupuje pliki według kategorii"""
        grouped_by_extension_category = defaultdict(list)
        grouped_by_name_category = defaultdict(list)
        grouped_by_size = defaultdict(list)
        grouped_by_age = defaultdict(list)
        grouped_by_dynamic = defaultdict(list)  # NOWE: grupy dynamiczne

        all_groups = defaultdict(list)

        for file_info in files_info_list:
            # Grupowanie według rozszerzenia
            ext_category = file_info.category_extension
            grouped_by_extension_category[ext_category].append(file_info)
            all_groups[f"rozszerzenie_{ext_category}"].append(file_info)

            # Grupowanie według kategorii nazwy
            for name_cat in file_info.category_name:
                grouped_by_name_category[name_cat].append(file_info)
                all_groups[f"nazwa_{name_cat}"].append(file_info)

                # Specjalne grupowanie dynamiczne
                if name_cat.startswith(('grupa_', 'seria_', 'temat_')):
                    grouped_by_dynamic[name_cat].append(file_info)

            # Pozostałe grupowania
            size_category = file_info.size_category
            grouped_by_size[size_category].append(file_info)
            all_groups[f"rozmiar_{size_category}"].append(file_info)

            age_category = file_info.date_category
            grouped_by_age[age_category].append(file_info)
            all_groups[f"wiek_{age_category}"].append(file_info)

        return {
            'według_rozszerzenia': grouped_by_extension_category,
            'według_nazwy': grouped_by_name_category,
            'według_rozmiaru': grouped_by_size,
            'według_wieku': grouped_by_age,
            'dynamiczne_grupy': grouped_by_dynamic,  # NOWE
            'wszystkie_grupy': all_groups
        }

    def get_dynamic_patterns_stats(self):
        """Zwraca statystyki dynamicznych wzorców"""
        if not self.dynamic_patterns:
            return "Brak wzorców dynamicznych"

        stats = f"Wzorce dynamiczne ({len(self.dynamic_patterns)} unikalnych):\n"
        top_patterns = sorted(self.dynamic_patterns.items(), key=lambda x: x[1], reverse=True)

        for pattern, count in top_patterns[:10]:
            stats += f"  {pattern}: {count} wystąpień\n"

        return stats

    def smart_group_files_by_name(self, files_info_list):
        """Inteligentne grupowanie na podstawie podobieństwa nazw"""
        groups = defaultdict(list)
        processed_files = set()

        for file_info in files_info_list:
            if file_info in processed_files:
                continue

            filename = file_info.name.lower()

            # Znajdź pliki o podobnych nazwach
            similar_files = [file_info]

            for other_file in files_info_list:
                if other_file != file_info and other_file not in processed_files:
                    other_name = other_file.name.lower()

                    # Sprawdź podobieństwo (wspólny prefiks/sufiks)
                    if self._files_are_similar(filename, other_name):
                        similar_files.append(other_file)
                        processed_files.add(other_file)

            # Utwórz grupę
            if len(similar_files) > 1:
                # Znajdź wspólną część nazwy
                common_part = self._find_common_part([f.name for f in similar_files])
                group_name = f"Seria: {common_part}" if common_part else f"Grupa: {file_info.name[:10]}"
                groups[group_name] = similar_files
            else:
                # Pojedynczy plik - grupuj według typu lub pierwszej kategorii
                if file_info.category_name:
                    category = file_info.category_name[0]
                    groups[f"Kategoria: {category}"].append(file_info)
                else:
                    groups["Różne"].append(file_info)

            processed_files.add(file_info)

        return dict(groups)

    def _files_are_similar(self, name1, name2):
        """Sprawdza czy nazwy plików są podobne"""
        # Usuń cyfry i znaki specjalne
        clean1 = re.sub(r'[^\w]', '', name1)
        clean2 = re.sub(r'[^\w]', '', name2)

        # Sprawdź wspólny prefiks (minimum 4 znaki)
        common_prefix_len = 0
        for c1, c2 in zip(clean1, clean2):
            if c1 == c2:
                common_prefix_len += 1
            else:
                break

        if common_prefix_len >= 4:
            return True

        # Sprawdź czy jeden zawiera drugi (dla dłuższych nazw)
        if len(clean1) >= 6 and len(clean2) >= 6:
            shorter = clean1 if len(clean1) < len(clean2) else clean2
            longer = clean2 if len(clean1) < len(clean2) else clean1

            if shorter in longer:
                return True

        return False

    def _find_common_part(self, names):
        """Znajduje wspólną część nazw"""
        if not names:
            return ""

        # Znajdź najdłuższy wspólny prefiks
        common = names[0]
        for name in names[1:]:
            new_common = ""
            for c1, c2 in zip(common, name):
                if c1.lower() == c2.lower():
                    new_common += c1
                else:
                    break
            common = new_common

        # Usuń końcowe cyfry i znaki specjalne
        common = re.sub(r'[\d_\-\s]+$', '', common)

        return common if len(common) >= 3 else ""