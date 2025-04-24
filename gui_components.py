# gui_components.py
import tkinter as tk
from tkinter import ttk, messagebox

from data_export import export_to_csv
from file_operations import select_files, select_destination, move_files


# Pozostałe funkcje bez zmian...

def show_files_table(files_info):
    """Funkcja wyświetlająca tabelę z informacjami o przeniesionych plikach"""
    if not files_info:
        messagebox.showinfo("Informacja", "Brak informacji o plikach do wyświetlenia.")
        return

    # Utworzenie nowego okna dla tabeli
    table_window = tk.Toplevel()
    table_window.title("Informacje o przeniesionych plikach")
    table_window.geometry("1200x600")  # Zwiększony rozmiar okna dla dodatkowych kolumn

    # Utworzenie notebooka (zakładek)
    notebook = ttk.Notebook(table_window)
    notebook.pack(fill="both", expand=True, padx=10, pady=10)

    # Zakładka 1: Podstawowe informacje
    basic_frame = ttk.Frame(notebook)
    notebook.add(basic_frame, text="Podstawowe informacje")

    # Zakładka 2: Zaawansowane informacje
    advanced_frame = ttk.Frame(notebook)
    notebook.add(advanced_frame, text="Zaawansowane informacje")

    # Utworzenie tabeli z podstawowymi informacjami
    basic_columns = (
        "Nazwa", "Rozszerzenie", "Status", "Czas operacji",
        "Rozmiar", "Data utworzenia", "Data modyfikacji", "Atrybuty"
    )
    basic_tree = ttk.Treeview(basic_frame, columns=basic_columns, show="headings")

    # Definicja nagłówków kolumn
    for col in basic_columns:
        basic_tree.heading(col, text=col)
        basic_tree.column(col, width=120)  # Dostosowanie szerokości kolumn

    # Dodanie danych do tabeli podstawowych informacji
    for file_info in files_info:
        basic_tree.insert("", "end", values=(
            file_info.name,
            file_info.extension,
            file_info.status,
            file_info.timestamp,
            format_size(file_info.file_size),
            file_info.creation_date,
            file_info.modification_date,
            file_info.attributes
        ))

    # Dodanie paska przewijania dla podstawowej tabeli
    basic_scrollbar_y = ttk.Scrollbar(basic_frame, orient="vertical", command=basic_tree.yview)
    basic_scrollbar_x = ttk.Scrollbar(basic_frame, orient="horizontal", command=basic_tree.xview)
    basic_tree.configure(yscrollcommand=basic_scrollbar_y.set, xscrollcommand=basic_scrollbar_x.set)
    basic_scrollbar_y.pack(side="right", fill="y")
    basic_scrollbar_x.pack(side="bottom", fill="x")
    basic_tree.pack(fill="both", expand=True)

    # Utworzenie tabeli z zaawansowanymi informacjami
    advanced_columns = (
        "Nazwa", "Rozszerzenie", "Typ MIME", "Sygnatura pliku", "Słowa kluczowe", "Informacje o nagłówkach"
    )
    advanced_tree = ttk.Treeview(advanced_frame, columns=advanced_columns, show="headings")

    # Definicja nagłówków kolumn dla zaawansowanych informacji
    for col in advanced_columns:
        advanced_tree.heading(col, text=col)
        if col in ["Słowa kluczowe", "Informacje o nagłówkach"]:
            advanced_tree.column(col, width=300)  # Szersze kolumny dla dłuższych tekstów
        else:
            advanced_tree.column(col, width=150)

    # Dodanie danych do tabeli zaawansowanych informacji
    for file_info in files_info:
        advanced_tree.insert("", "end", values=(
            file_info.name,
            file_info.extension,
            file_info.mime_type,
            file_info.file_signature,
            file_info.keywords,
            file_info.headers_info
        ))

    # Dodanie paska przewijania dla zaawansowanej tabeli
    advanced_scrollbar_y = ttk.Scrollbar(advanced_frame, orient="vertical", command=advanced_tree.yview)
    advanced_scrollbar_x = ttk.Scrollbar(advanced_frame, orient="horizontal", command=advanced_tree.xview)
    advanced_tree.configure(yscrollcommand=advanced_scrollbar_y.set, xscrollcommand=advanced_scrollbar_x.set)
    advanced_scrollbar_y.pack(side="right", fill="y")
    advanced_scrollbar_x.pack(side="bottom", fill="x")
    advanced_tree.pack(fill="both", expand=True)

    # Przycisk do eksportu danych
    export_button = tk.Button(
        table_window,
        text="Eksportuj do pliku CSV",
        command=lambda: export_to_csv(files_info)
    )
    export_button.pack(pady=10)