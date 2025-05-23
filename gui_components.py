# gui_components.py - Fixed GUI Components
import tkinter as tk
from tkinter import ttk, messagebox
from typing import List, Callable
from models import FileInfo
from data_export import export_to_csv
from file_group_visualizer import show_file_groups


class MainWindow:
    """Główne okno aplikacji"""

    def __init__(self, on_start_process: Callable):
        self.on_start_process = on_start_process
        self.root = self.create_window()
        self.setup_ui()

    def create_window(self) -> tk.Tk:
        """Tworzy główne okno"""
        root = tk.Tk()
        root.title("Organizator Plików")
        root.geometry("400x300")
        root.resizable(True, True)

        # Wyśrodkuj okno - poprawiona metoda
        self.center_window(root, 400, 300)

        return root

    def center_window(self, window, width, height):
        """Wyśrodkowuje okno na ekranie"""
        window.update_idletasks()
        screen_width = window.winfo_screenwidth()
        screen_height = window.winfo_screenheight()
        x = (screen_width // 2) - (width // 2)
        y = (screen_height // 2) - (height // 2)
        window.geometry(f"{width}x{height}+{x}+{y}")

    def setup_ui(self):
        """Konfiguruje interfejs użytkownika"""
        # Główna ramka
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill="both", expand=True)

        # Tytuł
        title_label = ttk.Label(
            main_frame,
            text="Organizator Plików",
            font=("Arial", 16, "bold")
        )
        title_label.pack(pady=(0, 20))

        # Opis
        desc_label = ttk.Label(
            main_frame,
            text="Program do organizacji i kategoryzacji plików\nz automatycznym wykrywaniem wzorców",
            justify="center",
            font=("Arial", 9)
        )
        desc_label.pack(pady=(0, 30))

        # Przycisk główny
        start_button = ttk.Button(
            main_frame,
            text="Rozpocznij Organizację Plików",
            command=self.on_start_process,
            style="Accent.TButton"
        )
        start_button.pack(fill="x", pady=(0, 10))

        # Ramka dodatkowych opcji
        options_frame = ttk.LabelFrame(main_frame, text="Opcje", padding="10")
        options_frame.pack(fill="x", pady=(10, 0))

        # Info o historii
        history_info = ttk.Label(
            options_frame,
            text="💡 Program zapamiętuje Twoje preferencje\ni automatycznie sugeruje najlepsze lokalizacje",
            justify="center",
            font=("Arial", 8),
            foreground="gray"
        )
        history_info.pack()

        # Przycisk zamknięcia
        close_button = ttk.Button(
            main_frame,
            text="Zamknij",
            command=self.root.destroy
        )
        close_button.pack(side="bottom", pady=(20, 0))

        # Konfiguracja stylów
        self._setup_styles()

    def _setup_styles(self):
        """Konfiguruje style TTK"""
        try:
            style = ttk.Style()
            style.theme_use('clam')
            style.configure('Accent.TButton', font=('Arial', 10, 'bold'))
        except:
            pass

    def run(self):
        """Uruchamia główną pętlę aplikacji"""
        self.root.mainloop()


class ResultsWindow:
    """Okno z wynikami operacji"""

    def __init__(self, parent, files_info: List[FileInfo]):
        self.parent = parent
        self.files_info = files_info
        self.window = None
        self.setup_window()
        self.setup_ui()
        self.populate_data()

    def setup_window(self):
        """Konfiguruje okno wyników"""
        self.window = tk.Toplevel(self.parent)
        self.window.title("Wyniki Operacji")
        self.window.geometry("900x600")
        self.window.transient(self.parent)
        self.window.grab_set()

        # Wyśrodkuj okno
        self.center_window(self.window, 900, 600)

    def center_window(self, window, width, height):
        """Wyśrodkowuje okno na ekranie"""
        window.update_idletasks()
        screen_width = window.winfo_screenwidth()
        screen_height = window.winfo_screenheight()
        x = (screen_width // 2) - (width // 2)
        y = (screen_height // 2) - (height // 2)
        window.geometry(f"{width}x{height}+{x}+{y}")

    def setup_ui(self):
        """Konfiguruje interfejs okna wyników"""
        # Główna ramka
        main_frame = ttk.Frame(self.window)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Nagłówek
        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill="x", pady=(0, 10))

        title_label = ttk.Label(
            header_frame,
            text="Wyniki Organizacji Plików",
            font=("Arial", 14, "bold")
        )
        title_label.pack(side="left")

        # Statystyki
        self.stats_label = ttk.Label(header_frame, text="", font=("Arial", 9))
        self.stats_label.pack(side="right")

        # Notebook z zakładkami
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill="both", expand=True)

        # Zakładka: Lista plików
        self.create_files_tab(notebook)

        # Zakładka: Grupy
        self.create_groups_tab(notebook)

        # Przyciski akcji
        self.create_action_buttons(main_frame)

    def create_files_tab(self, notebook):
        """Tworzy zakładkę z listą plików"""
        files_frame = ttk.Frame(notebook)
        notebook.add(files_frame, text="Lista Plików")

        # Tabela plików
        columns = ("Nazwa", "Rozszerzenie", "Kategoria", "Rozmiar", "Status")
        self.files_tree = ttk.Treeview(files_frame, columns=columns, show="headings")

        # Konfiguracja kolumn
        widths = {"Nazwa": 200, "Rozszerzenie": 80, "Kategoria": 100, "Rozmiar": 80, "Status": 100}
        for col in columns:
            self.files_tree.heading(col, text=col)
            self.files_tree.column(col, width=widths.get(col, 100))

        # Scrollbary
        v_scroll = ttk.Scrollbar(files_frame, orient="vertical", command=self.files_tree.yview)
        h_scroll = ttk.Scrollbar(files_frame, orient="horizontal", command=self.files_tree.xview)
        self.files_tree.configure(yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)

        # Pakowanie
        v_scroll.pack(side="right", fill="y")
        h_scroll.pack(side="bottom", fill="x")
        self.files_tree.pack(fill="both", expand=True, padx=5, pady=5)

    def create_groups_tab(self, notebook):
        """Tworzy zakładkę z grupami"""
        groups_frame = ttk.Frame(notebook)
        notebook.add(groups_frame, text="Podgląd Grup")

        # Informacja o grupach
        info_label = ttk.Label(
            groups_frame,
            text="Kliknij 'Pokaż Grupy' aby otworzyć zaawansowany wizualizer",
            font=("Arial", 10),
            foreground="blue"
        )
        info_label.pack(pady=20)

        # Przycisk do wizualizera
        show_groups_btn = ttk.Button(
            groups_frame,
            text="Otwórz Wizualizer Grup",
            command=self.show_groups_window
        )
        show_groups_btn.pack()

        # Szybki podgląd statystyk
        stats_text = tk.Text(groups_frame, height=15, wrap=tk.WORD)
        stats_text.pack(fill="both", expand=True, padx=20, pady=20)

        # Wypełnij podstawowymi statystykami
        self.populate_stats_preview(stats_text)

    def create_action_buttons(self, parent):
        """Tworzy przyciski akcji"""
        buttons_frame = ttk.Frame(parent)
        buttons_frame.pack(fill="x", pady=(10, 0))

        # Eksport do CSV
        export_btn = ttk.Button(
            buttons_frame,
            text="Eksportuj do CSV",
            command=self.export_results
        )
        export_btn.pack(side="left", padx=(0, 10))

        # Pokaż grupy
        groups_btn = ttk.Button(
            buttons_frame,
            text="Pokaż Grupy",
            command=self.show_groups_window
        )
        groups_btn.pack(side="left", padx=(0, 10))

        # Zamknij
        close_btn = ttk.Button(
            buttons_frame,
            text="Zamknij",
            command=self.window.destroy
        )
        close_btn.pack(side="right")

    def populate_data(self):
        """Wypełnia dane w tabeli"""
        # Wyczyść tabelę
        for item in self.files_tree.get_children():
            self.files_tree.delete(item)

        # Dodaj pliki
        for file_info in self.files_info:
            # Formatuj status
            status = file_info.status
            if status == "success":
                status = "✅ Pomyślnie"
            elif status == "skipped":
                status = "⏩ Pominięty"
            elif status.startswith("error"):
                status = f"❌ {status}"

            self.files_tree.insert("", "end", values=(
                file_info.name,
                file_info.extension,
                file_info.category,
                file_info.display_size,
                status
            ))

        # Aktualizuj statystyki
        self.update_stats()

    def update_stats(self):
        """Aktualizuje statystyki w nagłówku"""
        total = len(self.files_info)
        success = len([f for f in self.files_info if f.status == "success"])
        errors = len([f for f in self.files_info if f.status.startswith("error")])
        skipped = len([f for f in self.files_info if f.status == "skipped"])

        stats_text = f"Razem: {total} | Pomyślne: {success} | Błędy: {errors} | Pominięte: {skipped}"
        self.stats_label.config(text=stats_text)

    def populate_stats_preview(self, text_widget):
        """Wypełnia podgląd statystyk"""
        from collections import Counter

        # Statystyki kategorii
        categories = Counter(f.category for f in self.files_info)
        extensions = Counter(f.extension for f in self.files_info)
        statuses = Counter(f.status for f in self.files_info)

        stats_content = "📊 STATYSTYKI PLIKÓW\n\n"

        stats_content += "KATEGORIE:\n"
        for category, count in categories.most_common():
            stats_content += f"  {category}: {count} plików\n"

        stats_content += "\nROZSZERZENIA:\n"
        for ext, count in extensions.most_common(10):  # Top 10
            display_ext = ext if ext else "(brak)"
            stats_content += f"  {display_ext}: {count} plików\n"

        stats_content += "\nSTATUSY:\n"
        for status, count in statuses.items():
            stats_content += f"  {status}: {count} plików\n"

        # Całkowity rozmiar
        total_size = sum(f.size for f in self.files_info)
        if total_size > 1024 ** 3:
            size_str = f"{total_size / (1024 ** 3):.1f} GB"
        elif total_size > 1024 ** 2:
            size_str = f"{total_size / (1024 ** 2):.1f} MB"
        else:
            size_str = f"{total_size / 1024:.1f} KB"

        stats_content += f"\nŁĄCZNY ROZMIAR: {size_str}\n"

        text_widget.insert('1.0', stats_content)
        text_widget.config(state='disabled')

    def show_groups_window(self):
        """Otwiera okno wizualizera grup"""
        show_file_groups(self.window, self.files_info)

    def export_results(self):
        """Eksportuje wyniki do CSV"""
        export_to_csv(self.files_info)


class ProgressDialog:
    """Proste okno dialogowe postępu"""

    def __init__(self, parent, title="Postęp"):
        self.parent = parent
        self.window = None
        self.setup_window(title)

    def setup_window(self, title):
        """Konfiguruje okno postępu"""
        self.window = tk.Toplevel(self.parent)
        self.window.title(title)
        self.window.geometry("350x150")
        self.window.resizable(False, False)
        self.window.transient(self.parent)
        self.window.grab_set()

        # Wyśrodkuj okno
        self.center_window(self.window, 350, 150)

        # Ramka
        frame = ttk.Frame(self.window, padding="20")
        frame.pack(fill="both", expand=True)

        # Etykieta statusu
        self.status_label = ttk.Label(frame, text="Przetwarzanie...")
        self.status_label.pack(pady=(0, 10))

        # Pasek postępu
        self.progress = ttk.Progressbar(frame, mode='indeterminate')
        self.progress.pack(fill="x")
        self.progress.start()

    def center_window(self, window, width, height):
        """Wyśrodkowuje okno na ekranie"""
        window.update_idletasks()
        screen_width = window.winfo_screenwidth()
        screen_height = window.winfo_screenheight()
        x = (screen_width // 2) - (width // 2)
        y = (screen_height // 2) - (height // 2)
        window.geometry(f"{width}x{height}+{x}+{y}")

    def update_status(self, status: str):
        """Aktualizuje status"""
        if self.status_label and self.window:
            self.status_label.config(text=status)
            self.window.update()

    def close(self):
        """Zamyka okno dialogowe"""
        try:
            if self.progress:
                self.progress.stop()
            if self.window:
                self.window.destroy()
        except tk.TclError:
            # Okno już zostało zniszczone
            pass
        except Exception as e:
            print(f"Error closing progress dialog: {e}")


# Funkcje pomocnicze dla kompatybilności
def create_main_window():
    """Tworzy główne okno - funkcja pomocnicza"""
    root = tk.Tk()
    root.title("Organizator Plików")
    root.geometry("400x300")
    return root


def show_files_table(files_info: List[FileInfo], parent=None):
    """Wyświetla tabelę z wynikami - funkcja pomocnicza"""
    if parent is None:
        parent = tk.Tk()
        parent.withdraw()

    ResultsWindow(parent, files_info)