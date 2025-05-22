# enhanced_file_group_visualizer.py - POPRAWIONA WERSJA z czystym grupowaniem
import tkinter as tk
from tkinter import ttk, scrolledtext
from collections import defaultdict, Counter
import os
import re


def format_size(size_in_bytes):
    """Formatuje rozmiar w bajtach na bardziej czytelną formę"""
    if size_in_bytes < 1024:
        return f"{size_in_bytes} B"
    elif size_in_bytes < 1024 * 1024:
        return f"{size_in_bytes / 1024:.2f} KB"
    elif size_in_bytes < 1024 * 1024 * 1024:
        return f"{size_in_bytes / (1024 * 1024):.2f} MB"
    else:
        return f"{size_in_bytes / (1024 * 1024 * 1024):.2f} GB"


class EnhancedFileGroupVisualizer:
    """Ulepszona klasa do wizualizacji grup plików z CZYSTĄ logiką grupowania"""

    def __init__(self, parent, files_info, category_analyzer):
        self.parent = parent
        self.files_info = files_info
        self.category_analyzer = category_analyzer
        self.current_groups = {}
        self._updating = False  # Flaga blokująca wielokrotne wywołania

        # Utworzenie okna
        try:
            self.window = tk.Toplevel(parent)
            self.window.title("Wizualizacja grup plików")
            self.window.geometry("1400x900")
        except AttributeError:
            print("Creating new Tk root for visualization")
            root = tk.Tk()
            self.window = tk.Toplevel(root)
            self.window.title("Wizualizacja grup plików")
            self.window.geometry("1400x900")

        # Ustawienie stylu okna
        self.window.configure(bg='#f0f0f0')

        # Ramka główna
        self.main_frame = ttk.Frame(self.window)
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Banner informacyjny
        self.create_info_banner()

        # Ramka z selekcją metody grupowania
        self.group_selection_frame = ttk.LabelFrame(self.main_frame, text="Wybierz metodę grupowania")
        self.group_selection_frame.pack(fill="x", padx=5, pady=5)

        # Przełącznik wyboru metody grupowania
        self.group_by_var = tk.StringVar(value="rozszerzenie")
        group_methods = [
            ("Według rozszerzenia (.txt, .jpg...)", "rozszerzenie"),
            ("Według typu pliku (dokumenty, obrazy...)", "typ_pliku"),
            ("Według słów w nazwie", "slowa_nazwy"),
            ("Według rozmiaru pliku", "rozmiar"),
            ("Według daty utworzenia", "data"),
            ("Inteligentne grupy", "inteligentne"),
            ("Wszystkie kategorie", "wszystkie")
        ]

        # Utworzenie radiobutton dla każdej metody grupowania
        for i, (text, value) in enumerate(group_methods):
            rb = ttk.Radiobutton(
                self.group_selection_frame,
                text=text,
                value=value,
                variable=self.group_by_var,
                command=self.update_groups
            )
            rb.grid(row=i // 2, column=i % 2, padx=10, pady=5, sticky="w")

        # Informacja o inteligentnych grupach
        info_text = ("Inteligentne grupy: Automatycznie wykrywa podobne nazwy plików\n"
                     "i grupuje je razem (np. 'dokument1.txt', 'dokument2.txt')")

        info_label = ttk.Label(
            self.group_selection_frame,
            text=info_text,
            foreground="blue",
            font=("Arial", 9, "italic"),
            wraplength=600
        )
        info_label.grid(row=4, column=0, columnspan=2, padx=10, pady=5, sticky="w")

        # Ramka z wynikami grupowania
        self.results_frame = ttk.LabelFrame(self.main_frame, text="Wyniki grupowania")
        self.results_frame.pack(fill="both", expand=True, padx=5, pady=5)

        # Utworzenie panelów podzielonych
        self.paned_window = ttk.PanedWindow(self.results_frame, orient="horizontal")
        self.paned_window.pack(fill="both", expand=True, padx=5, pady=5)

        # Panel lewy - lista grup
        self.groups_frame = ttk.Frame(self.paned_window)
        self.paned_window.add(self.groups_frame, weight=1)

        # Panel prawy - szczegóły grupy
        self.details_frame = ttk.Frame(self.paned_window)
        self.paned_window.add(self.details_frame, weight=2)

        # Lista grup
        self.groups_label = ttk.Label(self.groups_frame, text="Grupy:", font=("Arial", 10, "bold"))
        self.groups_label.pack(fill="x", padx=5, pady=5)

        # Pole wyszukiwania grup
        search_frame = ttk.Frame(self.groups_frame)
        search_frame.pack(fill="x", padx=5, pady=2)

        ttk.Label(search_frame, text="Szukaj:").pack(side="left")
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(search_frame, textvariable=self.search_var)
        self.search_entry.pack(side="left", fill="x", expand=True, padx=(5, 0))
        self.search_var.trace('w', self.filter_groups)

        self.groups_listbox = tk.Listbox(self.groups_frame, font=("Arial", 9))
        self.groups_listbox.pack(fill="both", expand=True, padx=5, pady=5)
        self.groups_listbox.bind('<<ListboxSelect>>', self.show_group_details)

        # Pasek przewijania dla listy grup
        groups_scrollbar = ttk.Scrollbar(self.groups_frame, orient="vertical", command=self.groups_listbox.yview)
        self.groups_listbox.configure(yscrollcommand=groups_scrollbar.set)
        groups_scrollbar.pack(side="right", fill="y")

        # Etykieta dla szczegółów grupy
        self.details_label = ttk.Label(self.details_frame, text="Szczegóły grupy:", font=("Arial", 10, "bold"))
        self.details_label.pack(fill="x", padx=5, pady=5)

        # Obszar tekstowy dla informacji o grupie
        self.group_info_text = scrolledtext.ScrolledText(self.details_frame, height=6, wrap=tk.WORD, font=("Arial", 9))
        self.group_info_text.pack(fill="x", padx=5, pady=5)

        # Notebook dla różnych widoków szczegółów
        self.details_notebook = ttk.Notebook(self.details_frame)
        self.details_notebook.pack(fill="both", expand=True, padx=5, pady=5)

        # Zakładka 1: Lista plików
        self.files_tab = ttk.Frame(self.details_notebook)
        self.details_notebook.add(self.files_tab, text="Pliki w grupie")

        # Tabela plików w grupie
        self.details_columns = ("Nazwa", "Rozszerzenie", "Rozmiar", "Data utworzenia", "Status")
        self.details_tree = ttk.Treeview(self.files_tab, columns=self.details_columns, show="headings")

        # Nagłówki kolumn
        for col in self.details_columns:
            self.details_tree.heading(col, text=col)
            self.details_tree.column(col, width=150)

        # Pasek przewijania dla tabeli szczegółów
        details_scrollbar_y = ttk.Scrollbar(self.files_tab, orient="vertical", command=self.details_tree.yview)
        details_scrollbar_x = ttk.Scrollbar(self.files_tab, orient="horizontal", command=self.details_tree.xview)
        self.details_tree.configure(yscrollcommand=details_scrollbar_y.set, xscrollcommand=details_scrollbar_x.set)

        # Umieszczenie tabeli i pasków przewijania
        details_scrollbar_y.pack(side="right", fill="y")
        details_scrollbar_x.pack(side="bottom", fill="x")
        self.details_tree.pack(fill="both", expand=True, padx=5, pady=5)

        # Zakładka 2: Analiza grup
        self.analysis_tab = ttk.Frame(self.details_notebook)
        self.details_notebook.add(self.analysis_tab, text="Analiza grupy")

        # Obszar analizy grupy
        self.analysis_text = scrolledtext.ScrolledText(self.analysis_tab, wrap=tk.WORD, font=("Courier", 9))
        self.analysis_text.pack(fill="both", expand=True, padx=5, pady=5)

        # Panel statystyk
        self.stats_frame = ttk.LabelFrame(self.main_frame, text="Statystyki grupowania")
        self.stats_frame.pack(fill="x", padx=5, pady=5)

        # Tworzenie siatki dla statystyk
        stats_grid = ttk.Frame(self.stats_frame)
        stats_grid.pack(fill="x", padx=10, pady=5)

        # Pierwsza linia statystyk
        self.total_files_label = ttk.Label(stats_grid, text="Liczba plików: 0", font=("Arial", 9))
        self.total_files_label.grid(row=0, column=0, padx=10, pady=2, sticky="w")

        self.total_groups_label = ttk.Label(stats_grid, text="Liczba grup: 0", font=("Arial", 9))
        self.total_groups_label.grid(row=0, column=1, padx=10, pady=2, sticky="w")

        self.largest_group_label = ttk.Label(stats_grid, text="Największa grupa: -", font=("Arial", 9))
        self.largest_group_label.grid(row=0, column=2, padx=10, pady=2, sticky="w")

        self.method_info_label = ttk.Label(stats_grid, text="", foreground="green", font=("Arial", 9))
        self.method_info_label.grid(row=1, column=0, columnspan=3, padx=10, pady=2, sticky="w")

        # Przechowywanie pełnej listy grup dla filtrowania
        self.all_groups_list = []

        # Inicjalne grupowanie
        self.update_groups()

    def create_info_banner(self):
        """Tworzy banner informacyjny na górze okna"""
        banner_frame = ttk.Frame(self.main_frame)
        banner_frame.pack(fill="x", padx=5, pady=(0, 10))

        banner_label = ttk.Label(
            banner_frame,
            text="SYSTEM GRUPOWANIA PLIKÓW",
            font=("Arial", 12, "bold"),
            foreground="darkblue",
            background="lightblue",
            anchor="center"
        )
        banner_label.pack(fill="x", pady=5)

    def filter_groups(self, *args):
        """Filtruje grupy na podstawie wyszukiwanego tekstu"""
        search_term = self.search_var.get().lower()

        # Wyczyść listbox
        self.groups_listbox.delete(0, tk.END)

        # Dodaj pasujące grupy
        for group_name in self.all_groups_list:
            if search_term in group_name.lower():
                self.groups_listbox.insert(tk.END, group_name)

    def update_groups(self):
        """Aktualizacja grup na podstawie wybranej metody - POPRAWIONA WERSJA"""
        # Zabezpieczenie przed wielokrotnym wywołaniem
        if hasattr(self, '_updating') and self._updating:
            return

        self._updating = True

        try:
            print(f"\n=== CZYSTE GRUPOWANIE - AKTUALIZACJA ===")

            # Radykalne czyszczenie wszystkich elementów
            self.groups_listbox.delete(0, tk.END)
            self.group_info_text.delete('1.0', tk.END)
            self.analysis_text.delete('1.0', tk.END)
            self.search_var.set("")

            # Czyszczenie tabeli szczegółów
            for i in self.details_tree.get_children():
                self.details_tree.delete(i)

            # Czyszczenie przechowywanych danych
            self.all_groups_list = []
            self.current_groups = {}

            # Pobieranie wybranej metody grupowania
            group_by = self.group_by_var.get()
            print(f"Wybrana metoda grupowania: {group_by}")

            # CZYSTE grupowanie - każda metoda tworzy TYLKO SWOJE grupy
            method_info = ""

            if group_by == "rozszerzenie":
                # TYLKO rozszerzenia - nie mieszamy z innymi kategoriami!
                print("=== GRUPOWANIE WEDŁUG ROZSZERZENIA ===")
                for file_info in self.files_info:
                    ext = file_info.extension.lower() if file_info.extension else "(brak rozszerzenia)"
                    if ext not in self.current_groups:
                        self.current_groups[ext] = []
                    self.current_groups[ext].append(file_info)
                    print(f"Dodano {file_info.name} do grupy rozszerzenia: {ext}")

                method_info = "Grupowanie według rozszerzenia pliku (.txt, .jpg, .pdf...)"

            elif group_by == "typ_pliku":
                # TYLKO typy plików z category_extension
                print("=== GRUPOWANIE WEDŁUG TYPU PLIKU ===")
                for file_info in self.files_info:
                    file_type = file_info.category_extension
                    if file_type not in self.current_groups:
                        self.current_groups[file_type] = []
                    self.current_groups[file_type].append(file_info)
                    print(f"Dodano {file_info.name} do grupy typu: {file_type}")

                method_info = "Grupowanie według typu pliku (dokumenty, obrazy, audio...)"

            elif group_by == "slowa_nazwy":
                print("=== ULEPSZONE GRUPOWANIE WEDŁUG NAZW ===")

                # Rozbudowany słownik kategorii semantycznych
                semantic_categories = {
                    'przyroda': {
                        'keywords': ['zwierzę', 'roślina', 'natura', 'las', 'drzewo', 'kwiat', 'ptak',
                                     'ryba', 'owad', 'ssak', 'gad', 'płaz', 'fauna', 'flora', 'ekologia',
                                     'animal', 'plant', 'nature', 'forest', 'tree', 'flower', 'bird'],
                        'prefixes': ['bio', 'eco', 'zoo', 'bot']
                    },
                    'nauka': {
                        'keywords': ['fizyka', 'chemia', 'matematyka', 'biologia', 'informatyka', 'nauka',
                                     'eksperyment', 'badanie', 'analiza', 'teoria', 'wzór', 'równanie',
                                     'physics', 'chemistry', 'math', 'biology', 'science', 'research'],
                        'prefixes': ['lab', 'sci', 'mat', 'fiz', 'chem', 'bio']
                    },
                    'finanse': {
                        'keywords': ['faktura', 'rachunek', 'płatność', 'konto', 'bank', 'pieniądze',
                                     'budżet', 'wydatek', 'przychód', 'podatek', 'księgowość', 'bilans',
                                     'invoice', 'payment', 'account', 'money', 'budget', 'tax'],
                        'prefixes': ['fv', 'inv', 'pay', 'fin', 'acc']
                    },
                    'dokumenty_firmowe': {
                        'keywords': ['umowa', 'kontrakt', 'oferta', 'protokół', 'sprawozdanie', 'raport',
                                     'prezentacja', 'spotkanie', 'projekt', 'zlecenie', 'zamówienie',
                                     'contract', 'offer', 'report', 'presentation', 'meeting', 'project'],
                        'prefixes': ['doc', 'rep', 'prez', 'proj', 'meet']
                    },
                    'edukacja': {
                        'keywords': ['lekcja', 'kurs', 'szkolenie', 'wykład', 'egzamin', 'test', 'zadanie',
                                     'ćwiczenie', 'podręcznik', 'notatka', 'studium', 'seminarium',
                                     'lesson', 'course', 'training', 'lecture', 'exam', 'exercise'],
                        'prefixes': ['edu', 'kurs', 'szk', 'stud', 'learn']
                    },
                    'multimedia': {
                        'keywords': ['zdjęcie', 'foto', 'obraz', 'grafika', 'wideo', 'film', 'muzyka',
                                     'dźwięk', 'audio', 'klip', 'animacja', 'render', 'edycja',
                                     'photo', 'image', 'graphic', 'video', 'music', 'sound', 'animation'],
                        'prefixes': ['img', 'vid', 'aud', 'gfx', 'anim', 'foto']
                    },
                    'osobiste': {
                        'keywords': ['prywatne', 'osobiste', 'rodzina', 'wakacje', 'urodziny', 'ślub',
                                     'pamiątka', 'wspomnienie', 'dziennik', 'list', 'kartka',
                                     'private', 'personal', 'family', 'vacation', 'birthday', 'diary'],
                        'prefixes': ['priv', 'pers', 'my', 'moje']
                    },
                    'technologia': {
                        'keywords': ['kod', 'program', 'aplikacja', 'system', 'baza', 'serwer', 'sieć',
                                     'backup', 'kopia', 'instalacja', 'konfiguracja', 'skrypt',
                                     'code', 'app', 'system', 'database', 'server', 'network', 'script'],
                        'prefixes': ['app', 'sys', 'db', 'net', 'dev', 'prog']
                    }
                }

                # Funkcja do wykrywania najlepszego dopasowania semantycznego
                def find_semantic_category(filename):
                    filename_lower = filename.lower()
                    best_category = None
                    best_score = 0

                    for category, data in semantic_categories.items():
                        score = 0

                        # Sprawdź słowa kluczowe
                        for keyword in data['keywords']:
                            if keyword in filename_lower:
                                score += 3  # Pełne dopasowanie słowa
                            elif any(part.startswith(keyword[:4]) for part in filename_lower.split('_')):
                                score += 1  # Częściowe dopasowanie

                        # Sprawdź prefiksy
                        for prefix in data['prefixes']:
                            if filename_lower.startswith(prefix):
                                score += 2

                        if score > best_score:
                            best_score = score
                            best_category = category

                    return best_category if best_score > 0 else None

                # Funkcja do analizy wzorców numerycznych
                def analyze_numeric_pattern(filename):
                    # Wzorce do wykrycia
                    patterns = {
                        'wersja': r'v\d+|ver\d+|wersja\d+|version\d+',
                        'data': r'\d{4}[-_]\d{2}[-_]\d{2}|\d{2}[-_]\d{2}[-_]\d{4}',
                        'numer_seryjny': r'#\d+|nr\d+|no\d+',
                        'część': r'część\d+|part\d+|cz\d+|pt\d+',
                        'rozdział': r'rozdział\d+|chapter\d+|rozdz\d+|ch\d+'
                    }

                    for pattern_name, pattern in patterns.items():
                        if re.search(pattern, filename.lower()):
                            return pattern_name

                    # Sprawdź sekwencje numeryczne
                    if re.search(r'\d{2,}', filename):
                        return 'numeracja'

                    return None

                # Funkcja do wyodrębnienia wspólnego rdzenia nazwy
                def extract_common_stem(filenames):
                    if len(filenames) < 2:
                        return None

                    # Znajdź najdłuższy wspólny prefiks
                    common_prefix = os.path.commonprefix([f.lower() for f in filenames])

                    # Usuń końcowe cyfry i znaki specjalne
                    common_prefix = re.sub(r'[\d_\-\s]+$', '', common_prefix)

                    # Minimum 4 znaki dla sensownego rdzenia
                    if len(common_prefix) >= 4:
                        return common_prefix

                    return None

                # Grupowanie plików
                temp_groups = defaultdict(list)
                ungrouped_files = []
                processed_files = set()  # Zbiór przetworzonych plików

                for file_info in self.files_info:
                    # Sprawdź czy plik już został przetworzony
                    if file_info in processed_files:
                        continue

                    file_name_lower = file_info.name.lower()
                    grouped = False

                    # 1. Najpierw sprawdź kategorie semantyczne
                    semantic_cat = find_semantic_category(file_info.name)
                    if semantic_cat:
                        temp_groups[f"Kategoria: {semantic_cat.replace('_', ' ').title()}"].append(file_info)
                        processed_files.add(file_info)
                        grouped = True
                        continue

                    # 2. Sprawdź wzorce numeryczne
                    numeric_pattern = analyze_numeric_pattern(file_info.name)
                    if numeric_pattern:
                        temp_groups[f"Wzorzec: {numeric_pattern.replace('_', ' ').title()}"].append(file_info)
                        processed_files.add(file_info)
                        grouped = True
                        continue

                    # 3. Analiza prefiksów (4-8 znaków)
                    if not grouped:
                        for prefix_len in range(8, 3, -1):
                            if len(file_name_lower) >= prefix_len:
                                prefix = file_name_lower[:prefix_len]
                                # Sprawdź czy prefiks jest sensowny (zawiera litery)
                                if any(c.isalpha() for c in prefix):
                                    # Znajdź pliki z podobnym prefiksem
                                    similar_files = [f for f in self.files_info
                                                     if f.name.lower().startswith(
                                            prefix) and f != file_info and f not in processed_files]
                                    if len(similar_files) >= 1:  # Co najmniej 2 pliki razem
                                        group_name = f"Seria: {prefix.title()}"
                                        if group_name not in temp_groups:
                                            temp_groups[group_name] = []
                                        temp_groups[group_name].append(file_info)
                                        processed_files.add(file_info)
                                        grouped = True
                                        break

                    # 4. Jeśli nadal nie zgrupowane, szukaj podobieństwa w słowach
                    if not grouped:
                        words = re.findall(r'[a-zA-ZżółćęśąźńŻÓŁĆĘŚĄŹŃ]{4,}', file_name_lower)
                        for word in words:
                            if len(word) >= 4:  # Minimalna długość słowa
                                similar_files = [f for f in self.files_info
                                                 if
                                                 word in f.name.lower() and f != file_info and f not in processed_files]
                                if len(similar_files) >= 1:
                                    temp_groups[f"Zawiera: {word.title()}"].append(file_info)
                                    processed_files.add(file_info)
                                    grouped = True
                                    break

                    # Jeśli nie znaleziono grupy, dodaj do niezgrupowanych
                    if not grouped:
                        ungrouped_files.append(file_info)
                        processed_files.add(file_info)

                # Przepisz grupy do finalnego słownika, usuwając pojedyncze pliki
                for group_name, files in temp_groups.items():
                    # Usuń duplikaty w obrębie grupy
                    unique_files = list(dict.fromkeys(files))
                    if len(unique_files) > 1:
                        self.current_groups[group_name] = unique_files
                    else:
                        ungrouped_files.extend(unique_files)

                # Dodaj wszystkie niezgrupowane pliki do grupy "Inne"
                if ungrouped_files:
                    self.current_groups["Inne"] = ungrouped_files

                method_info = "Ulepszone grupowanie semantyczne według nazw plików"

            elif group_by == "rozmiar":
                # TYLKO kategorie rozmiaru
                print("=== GRUPOWANIE WEDŁUG ROZMIARU ===")
                for file_info in self.files_info:
                    size_category = file_info.size_category
                    if size_category not in self.current_groups:
                        self.current_groups[size_category] = []
                    self.current_groups[size_category].append(file_info)
                    print(f"Dodano {file_info.name} do grupy rozmiaru: {size_category}")

                method_info = "Grupowanie według rozmiaru pliku (małe, średnie, duże...)"

            elif group_by == "data":
                # TYLKO kategorie daty
                print("=== GRUPOWANIE WEDŁUG DATY ===")
                for file_info in self.files_info:
                    date_category = file_info.date_category
                    if date_category not in self.current_groups:
                        self.current_groups[date_category] = []
                    self.current_groups[date_category].append(file_info)
                    print(f"Dodano {file_info.name} do grupy daty: {date_category}")

                method_info = "Grupowanie według daty utworzenia/modyfikacji"

            elif group_by == "inteligentne":
                print("=== INTELIGENTNE GRUPOWANIE HYBRYDOWE ===")

                # Używa kombinacji wszystkich metod
                hybrid_groups = defaultdict(lambda: {'files': [], 'score': 0})

                # Analiza każdego pliku
                for file_info in self.files_info:
                    best_group = None
                    best_score = 0

                    # Sprawdź istniejące grupy
                    for group_name, group_data in hybrid_groups.items():
                        if not group_data['files']:
                            continue

                        # Oblicz podobieństwo do grupy
                        score = 0

                        # Podobieństwo rozszerzeń
                        if any(f.extension == file_info.extension for f in group_data['files']):
                            score += 10

                        # Podobieństwo typów
                        if any(f.category_extension == file_info.category_extension for f in group_data['files']):
                            score += 8

                        # Podobieństwo nazw (używając difflib)
                        from difflib import SequenceMatcher
                        for existing_file in group_data['files'][:5]:  # Sprawdź max 5 plików
                            similarity = SequenceMatcher(None, file_info.name.lower(),
                                                         existing_file.name.lower()).ratio()
                            if similarity > 0.6:
                                score += int(similarity * 20)

                        # Podobieństwo rozmiaru
                        if any(f.size_category == file_info.size_category for f in group_data['files']):
                            score += 5

                        if score > best_score:
                            best_score = score
                            best_group = group_name

                    # Jeśli znaleziono dobrą grupę
                    if best_group and best_score > 15:
                        hybrid_groups[best_group]['files'].append(file_info)
                        hybrid_groups[best_group]['score'] += best_score
                    else:
                        # Utwórz nową grupę
                        # Określ nazwę grupy na podstawie dominującej cechy
                        if file_info.category_name and len(file_info.category_name) > 0:
                            group_name = f"Grupa: {file_info.category_name[0].title()}"
                        elif len(file_info.name) > 6:
                            group_name = f"Seria: {file_info.name[:6].title()}"
                        else:
                            group_name = f"Typ: {file_info.category_extension}"

                        hybrid_groups[group_name]['files'].append(file_info)
                        hybrid_groups[group_name]['score'] = 10

                # Konwertuj na finalny format, łącząc małe grupy
                ungrouped = []
                for group_name, group_data in hybrid_groups.items():
                    if len(group_data['files']) > 1:
                        self.current_groups[group_name] = group_data['files']
                    else:
                        ungrouped.extend(group_data['files'])

                # Dodaj niezgrupowane do "Inne"
                if ungrouped:
                    self.current_groups["Inne"] = ungrouped

                method_info = "Inteligentne grupowanie hybrydowe - fuzja wszystkich metod"

            elif group_by == "wszystkie":
                # Mix wszystkich kategorii z prefiksami - ale każdy plik tylko raz w każdej kategorii
                print("=== WSZYSTKIE KATEGORIE RAZEM ===")

                for file_info in self.files_info:
                    # Rozszerzenie
                    ext = file_info.extension.lower() if file_info.extension else "(brak)"
                    ext_key = f"Rozszerzenie: {ext}"
                    if ext_key not in self.current_groups:
                        self.current_groups[ext_key] = []
                    self.current_groups[ext_key].append(file_info)

                    # Typ pliku
                    type_key = f"Typ: {file_info.category_extension}"
                    if type_key not in self.current_groups:
                        self.current_groups[type_key] = []
                    self.current_groups[type_key].append(file_info)

                    # Rozmiar
                    size_key = f"Rozmiar: {file_info.size_category}"
                    if size_key not in self.current_groups:
                        self.current_groups[size_key] = []
                    self.current_groups[size_key].append(file_info)

                    # Data
                    date_key = f"Wiek: {file_info.date_category}"
                    if date_key not in self.current_groups:
                        self.current_groups[date_key] = []
                    self.current_groups[date_key].append(file_info)

                method_info = "Wszystkie możliwe kategorie razem"

            # Dodanie grup do listy
            for group_name, files in sorted(self.current_groups.items()):
                display_name = f"{group_name} ({len(files)})"
                self.all_groups_list.append(display_name)
                self.groups_listbox.insert(tk.END, display_name)

            # Wymuszenie odświeżenia
            self.groups_listbox.update_idletasks()

            print(f"\n=== WYNIK GRUPOWANIA ===")
            print(f"Dodano {len(self.current_groups)} grup do listy")
            for group_name, files in self.current_groups.items():
                print(f"  Grupa '{group_name}': {len(files)} plików")

            # Aktualizacja statystyk
            self._update_stats(method_info)

            # Czyszczenie tabeli szczegółów
            for i in self.details_tree.get_children():
                self.details_tree.delete(i)

        finally:
            # Zawsze resetuj flagę
            self._updating = False

    def show_group_details(self, event):
        """Wyświetla szczegóły wybranej grupy"""
        # Pobierz wybraną grupę
        selection = self.groups_listbox.curselection()
        if not selection:
            return

        # Pobierz nazwę grupy (usuwając informację o liczbie plików)
        group_name_with_count = self.groups_listbox.get(selection[0])
        group_name = group_name_with_count.split(" (")[0]

        # Czyszczenie tabeli
        for i in self.details_tree.get_children():
            self.details_tree.delete(i)

        # Czyszczenie analizy
        self.analysis_text.delete('1.0', tk.END)

        # Dodanie plików z grupy
        if group_name in self.current_groups:
            files = self.current_groups[group_name]

            # Aktualizacja informacji o grupie
            self._show_group_info(group_name, files)

            # Dodaj analizę grupy
            self._show_group_analysis(group_name, files)

            # Dodanie plików do tabeli
            for file_info in files:
                self.details_tree.insert("", "end", values=(
                    file_info.name,
                    file_info.extension,
                    format_size(file_info.file_size),
                    file_info.creation_date,
                    file_info.status
                ))

    def _show_group_info(self, group_name, files):
        """Pokazuje informacje o grupie"""
        info_text = f"GRUPA: {group_name}\n\n"
        info_text += f"Liczba plików: {len(files)}\n"

        # Oblicz statystyki grupy
        total_size = sum(f.file_size for f in files)
        info_text += f"Łączny rozmiar: {format_size(total_size)}\n"

        # Statystyki rozszerzeń
        extensions = Counter(f.extension.lower() for f in files)
        most_common_ext = extensions.most_common(1)[0] if extensions else ("brak", 0)
        info_text += f"Dominujące rozszerzenie: {most_common_ext[0]} ({most_common_ext[1]} plików)\n"

        # Średnia długość nazwy
        avg_name_length = sum(len(f.name) for f in files) / len(files) if files else 0
        info_text += f"Średnia długość nazwy: {avg_name_length:.1f} znaków\n\n"

        # Lista kilku przykładowych plików
        info_text += "Przykładowe pliki:\n"
        for i, file_info in enumerate(files[:5], 1):
            info_text += f"{i}. {file_info.name}{file_info.extension}\n"

        if len(files) > 5:
            info_text += f"... i {len(files) - 5} więcej plików\n"

        # Aktualizuj obszar tekstowy
        self.group_info_text.delete('1.0', tk.END)
        self.group_info_text.insert('1.0', info_text)

    def _show_group_analysis(self, group_name, files):
        """Pokazuje analizę grupy"""
        analysis_text = f"ANALIZA GRUPY: {group_name}\n"
        analysis_text += "=" * 50 + "\n\n"

        # Analiza nazw plików
        analysis_text += "Analiza nazw:\n"
        file_names = [f.name for f in files]

        # Statystyki długości nazw
        name_lengths = [len(name) for name in file_names]
        analysis_text += f"• Długość nazw: min={min(name_lengths)}, max={max(name_lengths)}, śr={sum(name_lengths) / len(name_lengths):.1f}\n"

        # Analiza rozszerzeń
        analysis_text += f"\nAnaliza rozszerzeń:\n"
        extensions = Counter(f.extension.lower() for f in files)
        for ext, count in extensions.most_common():
            percentage = (count / len(files)) * 100
            analysis_text += f"• {ext or '(brak)'}: {count} plików ({percentage:.1f}%)\n"

        # Analiza rozmiarów
        analysis_text += f"\nAnaliza rozmiarów:\n"
        sizes = [f.file_size for f in files]
        total_size = sum(sizes)
        avg_size = total_size / len(sizes) if sizes else 0
        analysis_text += f"• Łączny rozmiar: {format_size(total_size)}\n"
        analysis_text += f"• Średni rozmiar: {format_size(avg_size)}\n"
        analysis_text += f"• Zakres: {format_size(min(sizes))} - {format_size(max(sizes))}\n"

        # Rekomendacje
        analysis_text += f"\nRekomendacje:\n"
        if len(files) > 10:
            analysis_text += "• Duża grupa - można podzielić na podgrupy\n"
        if len(set(f.extension for f in files)) == 1:
            analysis_text += "• Wszystkie pliki mają to samo rozszerzenie\n"
        if total_size > 100 * 1024 * 1024:  # 100MB
            analysis_text += "• Duży łączny rozmiar - sprawdź czy wszystkie pliki są potrzebne\n"

        self.analysis_text.insert('1.0', analysis_text)

    def _update_stats(self, method_info=""):
        """Aktualizacja statystyk"""
        total_files = len(self.files_info)
        total_groups = len(self.current_groups)

        # Znajdź największą grupę
        if total_groups > 0:
            group_sizes = {name: len(files) for name, files in self.current_groups.items()}
            largest_group = max(group_sizes.items(), key=lambda x: x[1])
            largest_group_name = largest_group[0]
            largest_group_size = largest_group[1]
        else:
            largest_group_name = "-"
            largest_group_size = 0

        # Aktualizacja podstawowych etykiet
        self.total_files_label.config(text=f"Liczba plików: {total_files}")
        self.total_groups_label.config(text=f"Liczba grup: {total_groups}")
        self.largest_group_label.config(text=f"Największa: {largest_group_name[:30]}... ({largest_group_size})")

        # Informacja o metodzie
        self.method_info_label.config(text=method_info)


# Dla kompatybilności wstecznej
FileGroupVisualizer = EnhancedFileGroupVisualizer