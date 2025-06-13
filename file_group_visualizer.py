# file_group_visualizer.py
import tkinter as tk
from tkinter import ttk
import os
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


class FileGroupVisualizer:
    """Klasa do wizualizacji grup plików z poprawną logiką"""

    def __init__(self, parent, files_info, category_analyzer):
        self.parent = parent
        self.files_info = files_info
        self.category_analyzer = category_analyzer
        self.current_groups = {}

        # Utworzenie okna
        try:
            self.window = tk.Toplevel(parent)
            self.window.title("Wizualizacja grup plików")
            self.window.geometry("1000x700")
        except AttributeError:
            print("Creating new Tk root for visualization")
            root = tk.Tk()
            self.window = tk.Toplevel(root)
            self.window.title("Wizualizacja grup plików")
            self.window.geometry("1000x700")

        # Ramka główna
        self.main_frame = ttk.Frame(self.window)
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=10)

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
            rb.grid(row=i // 3, column=i % 3, padx=10, pady=5, sticky="w")

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
        self.groups_label = ttk.Label(self.groups_frame, text="Grupy:")
        self.groups_label.pack(fill="x", padx=5, pady=5)

        self.groups_listbox = tk.Listbox(self.groups_frame)
        self.groups_listbox.pack(fill="both", expand=True, padx=5, pady=5)
        self.groups_listbox.bind('<<ListboxSelect>>', self.show_group_details)

        # Pasek przewijania dla listy grup
        groups_scrollbar = ttk.Scrollbar(self.groups_frame, orient="vertical", command=self.groups_listbox.yview)
        self.groups_listbox.configure(yscrollcommand=groups_scrollbar.set)
        groups_scrollbar.pack(side="right", fill="y")

        # Etykieta dla szczegółów grupy
        self.details_label = ttk.Label(self.details_frame, text="Szczegóły grupy:")
        self.details_label.pack(fill="x", padx=5, pady=5)

        # Tabela plików w grupie
        self.details_columns = ("Nazwa", "Rozszerzenie", "Rozmiar", "Data utworzenia", "Status")
        self.details_tree = ttk.Treeview(self.details_frame, columns=self.details_columns, show="headings")

        # Nagłówki kolumn
        for col in self.details_columns:
            self.details_tree.heading(col, text=col)
            self.details_tree.column(col, width=150)

        # Pasek przewijania dla tabeli szczegółów
        details_scrollbar_y = ttk.Scrollbar(self.details_frame, orient="vertical", command=self.details_tree.yview)
        details_scrollbar_x = ttk.Scrollbar(self.details_frame, orient="horizontal", command=self.details_tree.xview)
        self.details_tree.configure(yscrollcommand=details_scrollbar_y.set, xscrollcommand=details_scrollbar_x.set)

        # Umieszczenie tabeli i pasków przewijania
        details_scrollbar_y.pack(side="right", fill="y")
        details_scrollbar_x.pack(side="bottom", fill="x")
        self.details_tree.pack(fill="both", expand=True, padx=5, pady=5)

        # Panel statystyk
        self.stats_frame = ttk.LabelFrame(self.main_frame, text="Statystyki grupowania")
        self.stats_frame.pack(fill="x", padx=5, pady=5)

        # Etykiety statystyk
        self.total_files_label = ttk.Label(self.stats_frame, text="Liczba plików: 0")
        self.total_files_label.grid(row=0, column=0, padx=10, pady=5, sticky="w")

        self.total_groups_label = ttk.Label(self.stats_frame, text="Liczba grup: 0")
        self.total_groups_label.grid(row=0, column=1, padx=10, pady=5, sticky="w")

        self.largest_group_label = ttk.Label(self.stats_frame, text="Największa grupa: -")
        self.largest_group_label.grid(row=0, column=2, padx=10, pady=5, sticky="w")

        self.method_info_label = ttk.Label(self.stats_frame, text="", font=("Arial", 9))
        self.method_info_label.grid(row=1, column=0, columnspan=3, padx=10, pady=2, sticky="w")

        # Inicjalne grupowanie
        self.update_groups()

    def update_groups(self):
        """Aktualizuje listę grup na podstawie wybranej metody"""
        print(f"\n=== Aktualizacja grup ===")

        # Czyszczenie listy grup
        self.groups_listbox.delete(0, tk.END)

        # Pobieranie wybranej metody grupowania
        group_by = self.group_by_var.get()
        print(f"Wybrana metoda grupowania: {group_by}")

        # Tworzenie odpowiedniego słownika grupowania
        if group_by == "rozszerzenie":
            self.current_groups = self._group_by_extension()
            method_info = "Grupowanie według rozszerzenia pliku (.txt, .jpg, .pdf...)"

        elif group_by == "typ_pliku":
            self.current_groups = self._group_by_file_type()
            method_info = "Grupowanie według typu pliku (dokumenty, obrazy, audio...)"

        elif group_by == "slowa_nazwy":
            self.current_groups = self._group_by_name_words()
            method_info = "Grupowanie według słów występujących w nazwach plików"

        elif group_by == "rozmiar":
            self.current_groups = self._group_by_size()
            method_info = "Grupowanie według rozmiaru pliku (małe, średnie, duże...)"

        elif group_by == "data":
            self.current_groups = self._group_by_date()
            method_info = "Grupowanie według daty utworzenia/modyfikacji"

        elif group_by == "wszystkie":
            self.current_groups = self._group_all_categories()
            method_info = "Wszystkie możliwe kategorie razem"

        # Dodanie grup do listy
        for group_name, files in sorted(self.current_groups.items()):
            self.groups_listbox.insert(tk.END, f"{group_name} ({len(files)})")

        print(f"Dodano {len(self.current_groups)} grup do listy")

        # Aktualizacja statystyk
        self._update_stats(method_info)

        # Czyszczenie tabeli szczegółów
        for i in self.details_tree.get_children():
            self.details_tree.delete(i)

    def _group_by_extension(self):
        """Grupuje pliki według prostego rozszerzenia"""
        result = defaultdict(list)
        for file_info in self.files_info:
            ext = file_info.extension.lower() if file_info.extension else "(brak rozszerzenia)"
            result[ext].append(file_info)
        return result

    def _group_by_file_type(self):
        """Grupuje pliki według kategorii typu pliku"""
        result = defaultdict(list)
        for file_info in self.files_info:
            file_type = file_info.category_extension
            result[file_type].append(file_info)
        return result

    def _group_by_name_words(self):
        """Grupuje pliki według słów występujących w nazwach"""
        result = defaultdict(list)

        # Zdefiniuj prawdziwe wzorce nazw
        name_patterns = [
            'faktura', 'cv_resume', 'raport', 'backup', 'notatka', 'projekt',
            'dokumentacja', 'konfiguracja', 'prezentacja', 'umowa', 'oferta',
            'ankieta', 'zdjęcia', 'muzyka', 'wideo', 'szkic', 'książka', 'list',
            'prywatne', 'praca', 'szkoła', 'wydarzenie'
        ]

        for file_info in self.files_info:
            file_added_to_group = False

            if file_info.category_name:
                for category in file_info.category_name:
                    # Tylko prawdziwe wzorce nazw, nie sztuczne grupy
                    if (len(category) > 2 and
                            not category.startswith("słowo_") and
                            category in name_patterns):
                        result[category].append(file_info)
                        file_added_to_group = True
                        break

            if not file_added_to_group:
                result["Inne"].append(file_info)

        return result

    def _group_by_size(self):
        """Grupuje pliki według rozmiaru"""
        result = defaultdict(list)
        for file_info in self.files_info:
            size_category = file_info.size_category
            result[size_category].append(file_info)
        return result

    def _group_by_date(self):
        """Grupuje pliki według daty"""
        result = defaultdict(list)
        for file_info in self.files_info:
            date_category = file_info.date_category
            result[date_category].append(file_info)
        return result

    def _group_all_categories(self):
        """Grupuje według wszystkich kategorii razem"""
        result = defaultdict(list)

        for file_info in self.files_info:
            # Dodaj grupę według rozszerzenia
            ext = file_info.extension.lower() if file_info.extension else "(brak)"
            result[f"Rozszerzenie: {ext}"].append(file_info)

            # Dodaj grupę według typu pliku
            result[f"Typ: {file_info.category_extension}"].append(file_info)

            # Dodaj grupę według rozmiaru
            result[f"Rozmiar: {file_info.size_category}"].append(file_info)

            # Dodaj grupę według daty
            result[f"Wiek: {file_info.date_category}"].append(file_info)

        return result

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

        # Dodanie plików z grupy
        if group_name in self.current_groups:
            files = self.current_groups[group_name]
            for file_info in files:
                self.details_tree.insert("", "end", values=(
                    file_info.name,
                    file_info.extension,
                    format_size(file_info.file_size),
                    file_info.creation_date,
                    file_info.status
                ))

    def _update_stats(self, method_info=""):
        """Aktualizuje statystyki grupowania"""
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

        # Aktualizacja etykiet
        self.total_files_label.config(text=f"Liczba plików: {total_files}")
        self.total_groups_label.config(text=f"Liczba grup: {total_groups}")
        self.largest_group_label.config(text=f"Największa grupa: {largest_group_name} ({largest_group_size})")
        self.method_info_label.config(text=method_info)