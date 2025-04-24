
import os
import re
import json
from datetime import datetime
from collections import Counter, defaultdict

# Słownik rozszerzeń do kategorii plików
FILE_CATEGORIES = {
    'dokument': ['.txt', '.doc', '.docx', '.pdf', '.rtf', '.odt', '.md', '.tex'],
    'arkusz': ['.xls', '.xlsx', '.csv', '.ods', '.tsv'],
    'prezentacja': ['.ppt', '.pptx', '.odp', '.key'],
    'obraz': ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.svg', '.webp', '.ico', '.psd'],
    'audio': ['.mp3', '.wav', '.flac', '.aac', '.ogg', '.wma', '.m4a'],
    'wideo': ['.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm', '.m4v'],
    'archiwum': ['.zip', '.rar', '.7z', '.tar', '.gz', '.bz2', '.xz', '.iso'],
    'kod': ['.py', '.js', '.html', '.css', '.java', '.cpp', '.c', '.h', '.php', '.rb', '.go', '.ts'],
    'baza_danych': ['.db', '.sqlite', '.sql', '.mdb', '.accdb'],
    'wykonywalne': ['.exe', '.msi', '.bat', '.sh', '.cmd', '.app'],
    'projekt': ['.psd', '.ai', '.xd', '.sketch', '.fig', '.xcodeproj'],
    'ebook': ['.epub', '.mobi', '.azw', '.azw3', '.fb2']
}

# Odwrotny słownik dla szybkiego wyszukiwania
EXTENSION_TO_CATEGORY = {}
for category, extensions in FILE_CATEGORIES.items():
    for ext in extensions:
        EXTENSION_TO_CATEGORY[ext.lower()] = category

# Wzorce nazw plików dla dodatkowej kategoryzacji
NAME_PATTERNS = {
    'faktura': [r'faktura', r'rachunek', r'invoice', r'fv', r'paragon'],
    'cv': [r'cv', r'resume', r'życiorys', r'curriculum'],
    'raport': [r'raport', r'report', r'sprawozdanie', r'zestawienie'],
    'backup': [r'backup', r'kopia', r'archiwum', r'\bkopia zapasowa\b', r'\bkopia\b'],
    'notatka': [r'notatka', r'note', r'notes', r'uwagi'],
    'projekt': [r'projekt', r'project', r'^proj_', r'^prj_'],
    'dokumentacja': [r'dokumentacja', r'documentation', r'manual', r'instrukcja'],
    'konfiguracja': [r'config', r'konfiguracja', r'ustawienia', r'settings']
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
                    return json.load(f)
            except:
                return {'extensions': {}, 'patterns': {}, 'destinations': {}}
        return {'extensions': {}, 'patterns': {}, 'destinations': {}}

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

        results = {
            'kategoria_rozszerzenia': 'nieznana',
            'kategoria_nazwy': [],
            'sugerowane_lokalizacje': []
        }

        # Kategoria na podstawie rozszerzenia
        if extension in EXTENSION_TO_CATEGORY:
            results['kategoria_rozszerzenia'] = EXTENSION_TO_CATEGORY[extension]

        # Kategoria na podstawie wzorców w nazwie
        for pattern_name, patterns in NAME_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, name_lower):
                    results['kategoria_nazwy'].append(pattern_name)
                    break

        # NOWA FUNKCJONALNOŚĆ: Dynamicznie generuj kategorie z nazwy pliku
        # Dzielimy nazwę pliku na słowa używając różnych separatorów
        words_from_name = re.findall(r'[a-zA-ZżółćęśąźńŻÓŁĆĘŚĄŹŃ0-9]{3,}', name_lower)

        # Lista słów do pominięcia (stopwords)
        stopwords = {'plik', 'obraz', 'file', 'kopia', 'copy', 'nowy', 'new', 'img', 'image', 'doc', 'document'}

        # Dodaj znalezione słowa jako kategorie
        for word in words_from_name:
            if word not in stopwords and word not in results['kategoria_nazwy'] and len(word) >= 3:
                if not any(word in pattern for pattern_list in NAME_PATTERNS.values() for pattern in pattern_list):
                    results['kategoria_nazwy'].append(word)

        # Sugerowane lokalizacje na podstawie historii
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

        return results

    def get_suggested_destination(self, file_path):
        """Zwraca sugerowaną lokalizację docelową dla pliku"""
        categorization = self.categorize_file(file_path)
        suggestions = categorization['sugerowane_lokalizacje']

        if suggestions:
            return suggestions[0][0]  # Pierwsza sugerowana lokalizacja

        return None