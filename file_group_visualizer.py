# file_group_visualizer.py - corrected version
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
    """Klasa do wizualizacji grup plików"""

    def __init__(self, parent, files_info, category_analyzer):
        self.parent = parent
        self.files_info = files_info
        self.category_analyzer = category_analyzer
        self.grouped_files = None
        self.current_groups = {}

        # Utworzenie okna - FIX: ensure parent is a Tk object
        try:
            self.window = tk.Toplevel(parent)
            self.window.title("Wizualizacja grup plików")
            self.window.geometry("1000x700")
        except AttributeError:
            # If parent is not a proper Tk parent, create a new root
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
            ("Według rozszerzenia", "rozszerzenie"),
            ("Według kategorii rozszerzenia", "kategoria_rozszerzenia"),
            ("Według nazwy", "nazwa"),
            ("Według rozmiaru", "rozmiar"),
            ("Według daty", "data"),
            ("Według przedmiotu", "przedmiot"),
            ("Według wzorca czasowego", "wzorzec_czasowy"),
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
            rb.grid(row=i // 4, column=i % 4, padx=10, pady=5, sticky="w")

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

        self.smallest_group_label = ttk.Label(self.stats_frame, text="Najmniejsza grupa: -")
        self.smallest_group_label.grid(row=0, column=3, padx=10, pady=5, sticky="w")

        # Inicjalne grupowanie - ZMODYFIKOWANE
        self.grouped_files = self._create_grouped_files()
        self.update_groups()

    def _create_grouped_files(self):
        """Tworzy strukturę zgrupowanych plików na podstawie zapamiętanych kategorii"""
        # Inicjalizacja słowników dla różnych typów grupowania
        grouped_by_extension_category = defaultdict(list)
        grouped_by_name_category = defaultdict(list)
        grouped_by_size = defaultdict(list)
        grouped_by_age = defaultdict(list)
        grouped_by_subject = defaultdict(list)
        grouped_by_time_pattern = defaultdict(list)

        # Wszystkie grupy (do wyświetlenia sumarycznego)
        all_groups = defaultdict(list)

        for file_info in self.files_info:
            # Używamy już zapisanych kategorii zamiast ponownego kategoryzowania

            # Grupowanie według kategorii rozszerzenia
            ext_category = file_info.category_extension
            grouped_by_extension_category[ext_category].append(file_info)
            all_groups[f"rozszerzenie_{ext_category}"].append(file_info)

            # Grupowanie według kategorii nazwy
            for name_cat in file_info.category_name:
                grouped_by_name_category[name_cat].append(file_info)
                all_groups[f"nazwa_{name_cat}"].append(file_info)

            # Grupowanie według rozmiaru - KLUCZOWA ZMIANA
            size_category = file_info.size_category
            print(f"Grouping by size: {file_info.name}{file_info.extension} → {size_category}")
            grouped_by_size[size_category].append(file_info)
            all_groups[f"rozmiar_{size_category}"].append(file_info)

            # Grupowanie według wieku
            age_category = file_info.date_category
            grouped_by_age[age_category].append(file_info)
            all_groups[f"wiek_{age_category}"].append(file_info)

            # Grupowanie według przedmiotu
            for subject in file_info.subject_categories:
                grouped_by_subject[subject].append(file_info)
                all_groups[f"przedmiot_{subject}"].append(file_info)

            # Grupowanie według wzorca czasowego
            for time_pattern in file_info.time_pattern_categories:
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

    def update_groups(self):
        """Aktualizuje listę grup na podstawie wybranej metody"""
        print("\n=== START: UPDATING GROUPS ===")
        for idx, fi in enumerate(self.files_info):
            print(f"File {idx + 1}: {fi.name}{fi.extension}, size: {fi.file_size}, category: {fi.size_category}")

        # Czyszczenie listy grup
        self.groups_listbox.delete(0, tk.END)

        # Pobieranie wybranej metody grupowania
        group_by = self.group_by_var.get()

        # Tworzenie odpowiedniego słownika grupowania
        if group_by == "rozszerzenie":
            # Grupowanie po prostym rozszerzeniu
            self.current_groups = self._group_by_extension()
        elif group_by == "kategoria_rozszerzenia":
            # Grupowanie po kategorii rozszerzenia
            self.current_groups = self.grouped_files['według_rozszerzenia']
        elif group_by == "nazwa":
            # Grupowanie po kategoriach z nazwy
            self.current_groups = self.grouped_files['według_nazwy']
        elif group_by == "rozmiar":
            # Grupowanie po rozmiarze
            self.current_groups = self.grouped_files['według_rozmiaru']
        elif group_by == "data":
            # Grupowanie po dacie/wieku
            self.current_groups = self.grouped_files['według_wieku']
        elif group_by == "przedmiot":
            # Grupowanie po przedmiocie
            self.current_groups = self.grouped_files['według_przedmiotu']
        elif group_by == "wzorzec_czasowy":
            # Grupowanie po wzorcu czasowym
            self.current_groups = self.grouped_files['według_wzorca_czasowego']
        elif group_by == "wszystkie":
            # Wszystkie kategorie
            self.current_groups = self.grouped_files['wszystkie_grupy']

        # Dodanie grup do listy
        for group_name, files in sorted(self.current_groups.items()):
            self.groups_listbox.insert(tk.END, f"{group_name} ({len(files)})")

        # Aktualizacja statystyk
        self._update_stats()

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

    def _group_by_extension(self):
        """Grupuje pliki po rozszerzeniu"""
        result = defaultdict(list)
        for file_info in self.files_info:
            # Używamy samego rozszerzenia jako klucza
            ext = file_info.extension.lower() if file_info.extension else "(brak rozszerzenia)"
            result[ext].append(file_info)
        return result

    def _update_stats(self):
        """Aktualizuje statystyki grupowania"""
        total_files = len(self.files_info)
        total_groups = len(self.current_groups)

        # Znajdź największą i najmniejszą grupę
        if total_groups > 0:
            group_sizes = {name: len(files) for name, files in self.current_groups.items()}
            largest_group = max(group_sizes.items(), key=lambda x: x[1])
            smallest_group = min(group_sizes.items(), key=lambda x: x[1])

            largest_group_name = largest_group[0]
            largest_group_size = largest_group[1]

            smallest_group_name = smallest_group[0]
            smallest_group_size = smallest_group[1]
        else:
            largest_group_name = "-"
            largest_group_size = 0
            smallest_group_name = "-"
            smallest_group_size = 0

        # Aktualizacja etykiet
        self.total_files_label.config(text=f"Liczba plików: {total_files}")
        self.total_groups_label.config(text=f"Liczba grup: {total_groups}")
        self.largest_group_label.config(text=f"Największa grupa: {largest_group_name} ({largest_group_size})")
        self.smallest_group_label.config(text=f"Najmniejsza grupa: {smallest_group_name} ({smallest_group_size})")