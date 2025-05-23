# file_group_visualizer.py - Uproszczony wizualizer grup plików
import tkinter as tk
from tkinter import ttk
from collections import defaultdict
from typing import List, Dict
from models import FileInfo


class FileGroupVisualizer:
    """Uproszczony wizualizer grup plików"""

    def __init__(self, parent, files_info: List[FileInfo]):
        self.parent = parent
        self.files_info = files_info
        self.current_groups = {}
        self.setup_window()
        self.setup_ui()
        self.update_groups()

    def setup_window(self):
        """Konfiguruje okno wizualizera"""
        self.window = tk.Toplevel(self.parent)
        self.window.title("Grupy plików")
        self.window.geometry("800x600")
        self.window.transient(self.parent)

    def setup_ui(self):
        """Konfiguruje interfejs użytkownika"""
        # Główna ramka
        main_frame = ttk.Frame(self.window)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Ramka wyboru metody grupowania
        method_frame = ttk.LabelFrame(main_frame, text="Metoda grupowania")
        method_frame.pack(fill="x", pady=(0, 10))

        # Opcje grupowania
        self.group_method = tk.StringVar(value="category")
        methods = [
            ("Według kategorii", "category"),
            ("Według rozszerzenia", "extension"),
            ("Według rozmiaru", "size"),
            ("Według statusu", "status")
        ]

        for i, (text, value) in enumerate(methods):
            ttk.Radiobutton(
                method_frame,
                text=text,
                value=value,
                variable=self.group_method,
                command=self.update_groups
            ).grid(row=0, column=i, padx=10, pady=5, sticky="w")

        # Panel podzielony
        paned = ttk.PanedWindow(main_frame, orient="horizontal")
        paned.pack(fill="both", expand=True)

        # Lewa strona - lista grup
        left_frame = ttk.LabelFrame(paned, text="Grupy")
        paned.add(left_frame, weight=1)

        self.groups_listbox = tk.Listbox(left_frame)
        self.groups_listbox.pack(fill="both", expand=True, padx=5, pady=5)
        self.groups_listbox.bind('<<ListboxSelect>>', self.on_group_select)

        # Prawa strona - pliki w grupie
        right_frame = ttk.LabelFrame(paned, text="Pliki w grupie")
        paned.add(right_frame, weight=2)

        # Tabela plików
        columns = ("Nazwa", "Rozszerzenie", "Rozmiar", "Status")
        self.files_tree = ttk.Treeview(right_frame, columns=columns, show="headings")

        for col in columns:
            self.files_tree.heading(col, text=col)
            self.files_tree.column(col, width=120)

        # Scrollbary
        v_scroll = ttk.Scrollbar(right_frame, orient="vertical", command=self.files_tree.yview)
        h_scroll = ttk.Scrollbar(right_frame, orient="horizontal", command=self.files_tree.xview)
        self.files_tree.configure(yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)

        # Pakowanie
        v_scroll.pack(side="right", fill="y")
        h_scroll.pack(side="bottom", fill="x")
        self.files_tree.pack(fill="both", expand=True, padx=5, pady=5)

        # Panel statystyk
        stats_frame = ttk.LabelFrame(main_frame, text="Statystyki")
        stats_frame.pack(fill="x", pady=(10, 0))

        self.stats_label = ttk.Label(stats_frame, text="")
        self.stats_label.pack(pady=5)

    def update_groups(self):
        """Aktualizuje grupy na podstawie wybranej metody"""
        method = self.group_method.get()

        if method == "category":
            self.current_groups = self._group_by_category()
        elif method == "extension":
            self.current_groups = self._group_by_extension()
        elif method == "size":
            self.current_groups = self._group_by_size()
        elif method == "status":
            self.current_groups = self._group_by_status()

        # Aktualizuj listę grup
        self.groups_listbox.delete(0, tk.END)
        for group_name, files in sorted(self.current_groups.items()):
            self.groups_listbox.insert(tk.END, f"{group_name} ({len(files)})")

        # Aktualizuj statystyki
        self.update_stats()

        # Wyczyść tabelę plików
        for item in self.files_tree.get_children():
            self.files_tree.delete(item)

    def _group_by_category(self) -> Dict[str, List[FileInfo]]:
        """Grupuje pliki według kategorii"""
        groups = defaultdict(list)
        for file_info in self.files_info:
            groups[file_info.category].append(file_info)
        return dict(groups)

    def _group_by_extension(self) -> Dict[str, List[FileInfo]]:
        """Grupuje pliki według rozszerzenia"""
        groups = defaultdict(list)
        for file_info in self.files_info:
            ext = file_info.extension or "(brak)"
            groups[ext].append(file_info)
        return dict(groups)

    def _group_by_size(self) -> Dict[str, List[FileInfo]]:
        """Grupuje pliki według rozmiaru"""
        groups = defaultdict(list)
        for file_info in self.files_info:
            if file_info.size < 1024:
                category = "Małe (< 1KB)"
            elif file_info.size < 1024 ** 2:
                category = "Średnie (< 1MB)"
            elif file_info.size < 10 * 1024 ** 2:
                category = "Duże (< 10MB)"
            else:
                category = "Bardzo duże (> 10MB)"
            groups[category].append(file_info)
        return dict(groups)

    def _group_by_status(self) -> Dict[str, List[FileInfo]]:
        """Grupuje pliki według statusu"""
        groups = defaultdict(list)
        for file_info in self.files_info:
            status = file_info.status
            if status.startswith("error"):
                status = "Błędy"
            elif status == "success":
                status = "Pomyślne"
            elif status == "skipped":
                status = "Pominięte"
            else:
                status = "Inne"
            groups[status].append(file_info)
        return dict(groups)

    def on_group_select(self, event):
        """Obsługuje wybór grupy z listy"""
        selection = self.groups_listbox.curselection()
        if not selection:
            return

        # Pobierz nazwę grupy
        selected_text = self.groups_listbox.get(selection[0])
        group_name = selected_text.split(" (")[0]

        # Wyczyść tabelę
        for item in self.files_tree.get_children():
            self.files_tree.delete(item)

        # Dodaj pliki z wybranej grupy
        if group_name in self.current_groups:
            for file_info in self.current_groups[group_name]:
                self.files_tree.insert("", "end", values=(
                    file_info.name,
                    file_info.extension,
                    file_info.display_size,
                    file_info.status
                ))

    def update_stats(self):
        """Aktualizuje statystyki"""
        total_files = len(self.files_info)
        total_groups = len(self.current_groups)

        if total_groups > 0:
            largest_group_size = max(len(files) for files in self.current_groups.values())
            largest_group_name = next(
                name for name, files in self.current_groups.items()
                if len(files) == largest_group_size
            )
        else:
            largest_group_size = 0
            largest_group_name = "-"

        stats_text = (f"Plików: {total_files} | "
                      f"Grup: {total_groups} | "
                      f"Największa grupa: {largest_group_name} ({largest_group_size})")

        self.stats_label.config(text=stats_text)


class SimpleGrouper:
    """Prosta klasa do grupowania plików (bez GUI)"""

    @staticmethod
    def group_by_category(files: List[FileInfo]) -> Dict[str, List[FileInfo]]:
        """Grupuje pliki według kategorii"""
        groups = defaultdict(list)
        for file in files:
            groups[file.category].append(file)
        return dict(groups)

    @staticmethod
    def group_by_extension(files: List[FileInfo]) -> Dict[str, List[FileInfo]]:
        """Grupuje pliki według rozszerzenia"""
        groups = defaultdict(list)
        for file in files:
            ext = file.extension or "(brak)"
            groups[ext].append(file)
        return dict(groups)

    @staticmethod
    def group_by_size_category(files: List[FileInfo]) -> Dict[str, List[FileInfo]]:
        """Grupuje pliki według kategorii rozmiaru"""
        groups = defaultdict(list)
        for file in files:
            if file.size < 1024:
                category = "małe"
            elif file.size < 1024 ** 2:
                category = "średnie"
            else:
                category = "duże"
            groups[category].append(file)
        return dict(groups)


# Funkcje pomocnicze
def show_file_groups(parent, files_info: List[FileInfo]):
    """Wyświetla okno grupowania plików"""
    if not files_info:
        tk.messagebox.showinfo("Info", "Brak plików do grupowania")
        return

    FileGroupVisualizer(parent, files_info)


def create_simple_groups(files_info: List[FileInfo]) -> Dict[str, Dict[str, List[FileInfo]]]:
    """Tworzy podstawowe grupy plików"""
    return {
        'kategorie': SimpleGrouper.group_by_category(files_info),
        'rozszerzenia': SimpleGrouper.group_by_extension(files_info),
        'rozmiary': SimpleGrouper.group_by_size_category(files_info)
    }