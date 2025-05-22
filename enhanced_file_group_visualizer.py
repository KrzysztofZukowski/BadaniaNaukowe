# enhanced_file_group_visualizer.py - poprawiona wersja z logicznym grupowaniem
import tkinter as tk
from tkinter import ttk, scrolledtext
from collections import defaultdict, Counter


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
    """Ulepszona klasa do wizualizacji grup plików z poprawną logiką grupowania"""

    def __init__(self, parent, files_info, category_analyzer):
        self.parent = parent
        self.files_info = files_info
        self.category_analyzer = category_analyzer
        self.current_groups = {}

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
        """Aktualizacja grup na podstawie wybranej metody"""
        print(f"\n=== Aktualizacja grup ===")

        # Czyszczenie listy grup i pola wyszukiwania
        self.groups_listbox.delete(0, tk.END)
        self.group_info_text.delete('1.0', tk.END)
        self.analysis_text.delete('1.0', tk.END)
        self.search_var.set("")

        # Pobieranie wybranej metody grupowania
        group_by = self.group_by_var.get()
        print(f"Wybrana metoda grupowania: {group_by}")

        # CZYSTE grupowanie - każda metoda tworzy własne grupy od zera
        self.current_groups = {}

        if group_by == "rozszerzenie":
            # Tylko rozszerzenia - nic więcej!
            extensions_groups = defaultdict(list)
            for file_info in self.files_info:
                ext = file_info.extension.lower() if file_info.extension else "(brak rozszerzenia)"
                extensions_groups[ext].append(file_info)
            self.current_groups = dict(extensions_groups)
            method_info = "Grupowanie według rozszerzenia pliku (.txt, .jpg, .pdf...)"

        elif group_by == "typ_pliku":
            # Tylko typy plików z category_analyzer
            type_groups = defaultdict(list)
            for file_info in self.files_info:
                file_type = file_info.category_extension
                type_groups[file_type].append(file_info)
            self.current_groups = dict(type_groups)
            method_info = "Grupowanie według typu pliku (dokumenty, obrazy, audio...)"

        elif group_by == "slowa_nazwy":
            # Tylko prawdziwe wzorce nazw z NAME_PATTERNS
            name_groups = defaultdict(list)
            valid_patterns = [
                'faktura', 'cv_resume', 'raport', 'backup', 'notatka', 'projekt',
                'dokumentacja', 'konfiguracja', 'prezentacja', 'umowa', 'oferta',
                'ankieta', 'zdjęcia', 'muzyka', 'wideo', 'szkic', 'książka', 'list',
                'prywatne', 'praca', 'szkoła', 'wydarzenie'
            ]

            # DEBUGOWANIE - sprawdźmy co faktycznie mamy w kategoriach nazw
            print(f"\n=== DEBUGOWANIE KATEGORII NAZW ===")
            for file_info in self.files_info:
                print(f"Plik: {file_info.name}{file_info.extension}")
                print(f"  category_name: {file_info.category_name}")
                print(f"  Typ category_name: {type(file_info.category_name)}")
                if file_info.category_name:
                    for cat in file_info.category_name:
                        print(f"    - '{cat}' (długość: {len(cat)})")
                        if cat in valid_patterns:
                            print(f"      ✅ PASUJE do wzorców!")
                        else:
                            print(f"      ❌ NIE PASUJE do wzorców")
                print()

            for file_info in self.files_info:
                file_added = False
                if file_info.category_name:
                    for category in file_info.category_name:
                        # Sprawdź czy kategoria pasuje do wzorców (elastycznie)
                        if category in valid_patterns:
                            name_groups[category].append(file_info)
                            file_added = True
                            print(f"✅ Dodano {file_info.name} do grupy '{category}'")
                            break
                        # Sprawdź też czy kategoria zawiera wzorzec
                        elif any(pattern in category.lower() for pattern in valid_patterns):
                            matching_pattern = next(
                                pattern for pattern in valid_patterns if pattern in category.lower())
                            name_groups[matching_pattern].append(file_info)
                            file_added = True
                            print(
                                f"✅ Dodano {file_info.name} do grupy '{matching_pattern}' (przez zawartość w '{category}')")
                            break

                if not file_added:
                    name_groups["Inne"].append(file_info)
                    print(f"❌ Dodano {file_info.name} do grupy 'Inne'")

            print(f"\n=== WYNIK GRUPOWANIA NAZW ===")
            for group_name, files in name_groups.items():
                print(f"Grupa '{group_name}': {len(files)} plików")

            self.current_groups = dict(name_groups)
            method_info = "Grupowanie według słów występujących w nazwach plików"

        elif group_by == "rozmiar":
            # Tylko kategorie rozmiaru
            size_groups = defaultdict(list)
            for file_info in self.files_info:
                size_category = file_info.size_category
                size_groups[size_category].append(file_info)
            self.current_groups = dict(size_groups)
            method_info = "Grupowanie według rozmiaru pliku (małe, średnie, duże...)"

        elif group_by == "data":
            # Tylko kategorie daty
            date_groups = defaultdict(list)
            for file_info in self.files_info:
                date_category = file_info.date_category
                date_groups[date_category].append(file_info)
            self.current_groups = dict(date_groups)
            method_info = "Grupowanie według daty utworzenia/modyfikacji"

        elif group_by == "inteligentne":
            # Tylko inteligentne grupowanie
            smart_groups = {}
            try:
                if hasattr(self.category_analyzer, 'smart_group_files_by_name'):
                    temp_groups = self.category_analyzer.smart_group_files_by_name(self.files_info)
                    for group_name, files in temp_groups.items():
                        if group_name.startswith("Podobne_"):
                            clean_name = group_name.replace("Podobne_", "").split(" [")[0].strip()
                            smart_groups[f"Podobne: {clean_name}"] = files
                        elif group_name.startswith("Semantyczne_"):
                            clean_name = group_name.replace("Semantyczne_", "").split(" (")[0].strip()
                            smart_groups[f"Znaczenie: {clean_name}"] = files
                        elif group_name.startswith("Hybrydowe_"):
                            clean_name = group_name.replace("Hybrydowe_", "").split(" (")[0].strip()
                            smart_groups[f"Hybrydowe: {clean_name}"] = files
                else:
                    # Fallback - proste grupowanie podobieństwa
                    prefix_groups = defaultdict(list)
                    for file_info in self.files_info:
                        if len(file_info.name) >= 3:
                            prefix = file_info.name[:3].lower()
                            prefix_groups[prefix].append(file_info)

                    for prefix, files in prefix_groups.items():
                        if len(files) > 1:
                            smart_groups[f"Prefiks: {prefix}"] = files

            except Exception as e:
                print(f"Błąd inteligentnego grupowania: {e}")
                smart_groups["Błąd grupowania"] = self.files_info

            self.current_groups = smart_groups
            method_info = "Inteligentne grupowanie - automatyczne wykrywanie podobnych nazw"

        elif group_by == "wszystkie":
            # Mix wszystkich kategorii z prefiksami
            all_groups = {}

            # Rozszerzenia
            for file_info in self.files_info:
                ext = file_info.extension.lower() if file_info.extension else "(brak)"
                key = f"Rozszerzenie: {ext}"
                if key not in all_groups:
                    all_groups[key] = []
                all_groups[key].append(file_info)

            # Typy plików
            for file_info in self.files_info:
                key = f"Typ: {file_info.category_extension}"
                if key not in all_groups:
                    all_groups[key] = []
                all_groups[key].append(file_info)

            # Rozmiary
            for file_info in self.files_info:
                key = f"Rozmiar: {file_info.size_category}"
                if key not in all_groups:
                    all_groups[key] = []
                all_groups[key].append(file_info)

            self.current_groups = all_groups
            method_info = "Wszystkie możliwe kategorie razem"

        # Dodanie grup do listy
        self.all_groups_list = []
        for group_name, files in sorted(self.current_groups.items()):
            display_name = f"{group_name} ({len(files)})"
            self.all_groups_list.append(display_name)
            self.groups_listbox.insert(tk.END, display_name)

        print(f"Dodano {len(self.current_groups)} grup do listy")
        print(f"Grupy: {list(self.current_groups.keys())}")

        # Aktualizacja statystyk
        self._update_stats(method_info)

        # Czyszczenie tabeli szczegółów
        for i in self.details_tree.get_children():
            self.details_tree.delete(i)

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