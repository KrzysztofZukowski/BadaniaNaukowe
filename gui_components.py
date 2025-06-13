# gui_components.py
import tkinter as tk
from tkinter import ttk, messagebox
from data_export import export_to_csv
import traceback

# Importuj funkcję formatowania rozmiaru
from file_size_reader import FileSizeReader


def format_size(size_in_bytes):
    """Formatuje rozmiar w bajtach na bardziej czytelną formę używając klasy FileSizeReader"""
    return FileSizeReader.format_size(size_in_bytes)


def create_main_window():
    """Tworzy i konfiguruje główne okno aplikacji"""
    root = tk.Tk()
    root.title("Przenoszenie plików")
    root.geometry("400x200")
    return root


def setup_ui(root, start_moving_process):
    """Konfiguruje elementy interfejsu użytkownika w głównym oknie"""
    # Etykieta informacyjna
    label = tk.Label(root, text="Program do przenoszenia plików", font=("Arial", 14))
    label.pack(pady=10)

    # Przycisk do wyboru plików
    select_files_button = tk.Button(
        root,
        text="Wybierz pliki do przeniesienia",
        command=start_moving_process
    )
    select_files_button.pack(pady=10)

    # Przycisk zamknięcia
    close_button = tk.Button(
        root,
        text="Zamknij",
        command=root.destroy
    )
    close_button.pack(pady=10)


def show_files_table_inline(files_info, category_analyzer, parent_frame):
    """Funkcja wyświetlająca tabelę z informacjami o przeniesionych plikach w podanej ramce"""
    print("\n=== Wyświetlanie tabeli plików w głównym oknie ===")

    if not files_info:
        print("Brak informacji o plikach do wyświetlenia.")
        messagebox.showinfo("Informacja", "Brak informacji o plikach do wyświetlenia.")
        return

    if not parent_frame:
        print("Brak ramki nadrzędnej do wyświetlenia szczegółów.")
        return

    print(f"Liczba plików do wyświetlenia: {len(files_info)}")

    # Wyczyść poprzednią zawartość ramki
    for widget in parent_frame.winfo_children():
        widget.destroy()

    # Tytuł
    title_label = ttk.Label(parent_frame,
                           text=f"📊 SZCZEGÓŁY PLIKÓW ({len(files_info)})",
                           font=("Arial", 12, "bold"),
                           foreground="darkblue")
    title_label.pack(pady=(0, 10))

    # Utworzenie notebooka (zakładek)
    notebook = ttk.Notebook(parent_frame)
    notebook.pack(fill="both", expand=True, padx=5, pady=5)

    # Zakładka 1: Podstawowe informacje
    basic_frame = ttk.Frame(notebook)
    notebook.add(basic_frame, text="Podstawowe informacje")

    # Zakładka 2: Zaawansowane informacje
    advanced_frame = ttk.Frame(notebook)
    notebook.add(advanced_frame, text="Zaawansowane informacje")

    # Zakładka 3: Kategorie
    category_frame = ttk.Frame(notebook)
    notebook.add(category_frame, text="Kategorie")

    # Zakładka 4: Grupowanie
    grouping_frame = ttk.Frame(notebook)
    notebook.add(grouping_frame, text="Grupowanie")

    # Utworzenie tabeli z podstawowymi informacjami
    basic_columns = (
        "Nazwa", "Rozszerzenie", "Status", "Czas operacji",
        "Rozmiar", "Data utworzenia", "Data modyfikacji", "Atrybuty"
    )
    basic_tree = ttk.Treeview(basic_frame, columns=basic_columns, show="headings", height=10)

    # Definicja nagłówków kolumn
    for col in basic_columns:
        basic_tree.heading(col, text=col)
        basic_tree.column(col, width=120)

    # Dodanie danych do tabeli podstawowych informacji
    print("\nDodawanie danych do tabeli podstawowych informacji:")
    for idx, file_info in enumerate(files_info):
        try:
            # Próba sformatowania rozmiaru
            try:
                formatted_size = format_size(file_info.file_size)
            except Exception as size_error:
                print(f"Błąd formatowania rozmiaru dla {file_info.name}: {size_error}")
                formatted_size = "Błąd"

            values = (
                file_info.name,
                file_info.extension,
                file_info.status,
                file_info.timestamp,
                formatted_size,
                file_info.creation_date,
                file_info.modification_date,
                file_info.attributes
            )

            basic_tree.insert("", "end", values=values)
        except Exception as e:
            print(f"BŁĄD podczas dodawania do tabeli: {e}")
            traceback.print_exc()

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
    advanced_tree = ttk.Treeview(advanced_frame, columns=advanced_columns, show="headings", height=10)

    # Definicja nagłówków kolumn dla zaawansowanych informacji
    for col in advanced_columns:
        advanced_tree.heading(col, text=col)
        if col in ["Słowa kluczowe", "Informacje o nagłówkach"]:
            advanced_tree.column(col, width=300)
        else:
            advanced_tree.column(col, width=150)

    # Dodanie danych do tabeli zaawansowanych informacji
    for idx, file_info in enumerate(files_info):
        try:
            values = (
                file_info.name,
                file_info.extension,
                file_info.mime_type,
                file_info.file_signature,
                file_info.keywords,
                file_info.headers_info
            )
            advanced_tree.insert("", "end", values=values)
        except Exception as e:
            print(f"BŁĄD podczas dodawania do tabeli zaawansowanej: {e}")
            traceback.print_exc()

    # Dodanie paska przewijania dla zaawansowanej tabeli
    advanced_scrollbar_y = ttk.Scrollbar(advanced_frame, orient="vertical", command=advanced_tree.yview)
    advanced_scrollbar_x = ttk.Scrollbar(advanced_frame, orient="horizontal", command=advanced_tree.xview)
    advanced_tree.configure(yscrollcommand=advanced_scrollbar_y.set, xscrollcommand=advanced_scrollbar_x.set)
    advanced_scrollbar_y.pack(side="right", fill="y")
    advanced_scrollbar_x.pack(side="bottom", fill="x")
    advanced_tree.pack(fill="both", expand=True)

    # Utworzenie tabeli z informacjami o kategoriach
    category_columns = (
        "Nazwa", "Rozszerzenie", "Typ pliku", "Kategoria rozmiaru", "Kategoria daty", "Kategorie z nazwy"
    )
    category_tree = ttk.Treeview(category_frame, columns=category_columns, show="headings", height=10)

    # Definicja nagłówków kolumn dla kategorii
    for col in category_columns:
        category_tree.heading(col, text=col)
        if col in ["Kategorie z nazwy"]:
            category_tree.column(col, width=300)
        else:
            category_tree.column(col, width=150)

    # Dodanie danych do tabeli kategorii
    for idx, file_info in enumerate(files_info):
        try:
            # Formatowanie listy kategorii z nazwy
            try:
                name_categories = ", ".join(file_info.category_name) if file_info.category_name else "Brak"
            except Exception as cat_error:
                print(f"Błąd formatowania kategorii z nazwy: {cat_error}")
                name_categories = "Błąd"

            values = (
                file_info.name,
                file_info.extension,
                file_info.category_extension,
                file_info.size_category,
                file_info.date_category,
                name_categories
            )

            category_tree.insert("", "end", values=values)
        except Exception as e:
            print(f"BŁĄD podczas dodawania do tabeli kategorii: {e}")
            traceback.print_exc()

    # Dodanie paska przewijania dla tabeli kategorii
    category_scrollbar_y = ttk.Scrollbar(category_frame, orient="vertical", command=category_tree.yview)
    category_scrollbar_x = ttk.Scrollbar(category_frame, orient="horizontal", command=category_tree.xview)
    category_tree.configure(yscrollcommand=category_scrollbar_y.set, xscrollcommand=category_scrollbar_x.set)
    category_scrollbar_y.pack(side="right", fill="y")
    category_scrollbar_x.pack(side="bottom", fill="x")
    category_tree.pack(fill="both", expand=True)

    # Zakładka grupowania - uproszczona
    print("\nTworzenie zakładki grupowania...")

    # Tworzenie prostego grupowania
    try:
        simple_groups = create_simple_grouping(files_info)

        # Utworzenie widoku drzewa do wyświetlenia grup plików
        group_tree = ttk.Treeview(grouping_frame, show="tree headings", height=10)
        group_tree.heading("#0", text="Grupy plików")
        group_tree.column("#0", width=400)

        # Dodanie głównych kategorii grupowania
        extension_node = group_tree.insert("", "end", text="Według rozszerzenia", open=True)
        type_node = group_tree.insert("", "end", text="Według typu pliku", open=True)
        size_node = group_tree.insert("", "end", text="Według rozmiaru", open=True)
        date_node = group_tree.insert("", "end", text="Według daty", open=True)

        # Pomocnicza funkcja do dodawania plików do grupy
        def add_files_to_group(parent_node, category, files):
            try:
                group_node = group_tree.insert(parent_node, "end", text=f"{category} ({len(files)})", open=False)
                for file in files[:10]:  # Pokaż tylko pierwsze 10 plików
                    group_tree.insert(group_node, "end", text=f"{file.name}{file.extension}")
                if len(files) > 10:
                    group_tree.insert(group_node, "end", text=f"... i {len(files) - 10} więcej")
            except Exception as group_error:
                print(f"Błąd dodawania grupy: {group_error}")

        # Wypełnianie drzewa dla każdej kategorii grupowania
        print("Wypełnianie drzewa grupowania:")

        # Według rozszerzenia
        try:
            for category, files in simple_groups['extension'].items():
                add_files_to_group(extension_node, category, files)
        except Exception as ext_error:
            print(f"Błąd dodawania grup według rozszerzenia: {ext_error}")

        # Według typu pliku
        try:
            for category, files in simple_groups['type'].items():
                add_files_to_group(type_node, category, files)
        except Exception as type_error:
            print(f"Błąd dodawania grup według typu: {type_error}")

        # Według rozmiaru
        try:
            for category, files in simple_groups['size'].items():
                add_files_to_group(size_node, category, files)
        except Exception as size_error:
            print(f"Błąd dodawania grup według rozmiaru: {size_error}")

        # Według daty
        try:
            for category, files in simple_groups['date'].items():
                add_files_to_group(date_node, category, files)
        except Exception as date_error:
            print(f"Błąd dodawania grup według daty: {date_error}")

    except Exception as e:
        print(f"BŁĄD podczas tworzenia drzewa grup: {e}")
        traceback.print_exc()
        # Dodaj prostą etykietę w przypadku błędu
        error_label = ttk.Label(grouping_frame, text="Nie udało się wygenerować grup")
        error_label.pack()

    # Dodanie paska przewijania dla drzewa grupowania
    try:
        group_scrollbar_y = ttk.Scrollbar(grouping_frame, orient="vertical", command=group_tree.yview)
        group_scrollbar_x = ttk.Scrollbar(grouping_frame, orient="horizontal", command=group_tree.xview)
        group_tree.configure(yscrollcommand=group_scrollbar_y.set, xscrollcommand=group_scrollbar_x.set)
        group_scrollbar_y.pack(side="right", fill="y")
        group_scrollbar_x.pack(side="bottom", fill="x")
        group_tree.pack(fill="both", expand=True)
    except:
        print("Błąd podczas dodawania pasków przewijania")

    # Ramka przycisków na dole
    buttons_frame = ttk.Frame(parent_frame)
    buttons_frame.pack(fill="x", pady=(10, 0))

    # Przycisk do eksportu danych
    export_button = ttk.Button(
        buttons_frame,
        text="📊 Eksportuj do pliku CSV",
        command=lambda: export_to_csv(files_info)
    )
    export_button.pack(side="left", padx=(0, 10))

    # Statystyki
    stats_label = ttk.Label(
        buttons_frame,
        text=f"Plików: {len(files_info)} | "
             f"Pomyślnie: {len([f for f in files_info if 'przeniesiono' in f.status.lower() or f.status == 'Do organizacji'])} | "
             f"Błędy: {len([f for f in files_info if 'błąd' in f.status.lower()])}",
        font=("Arial", 9),
        foreground="blue"
    )
    stats_label.pack(side="right")

    print("Zakończono tworzenie interfejsu tabeli plików w głównym oknie")


def show_files_table(files_info, category_analyzer):
    """Funkcja wyświetlająca tabelę z informacjami o przeniesionych plikach - zachowana dla kompatybilności"""
    print("\n=== Wyświetlanie tabeli plików ===")

    if not files_info:
        print("Brak informacji o plikach do wyświetlenia.")
        messagebox.showinfo("Informacja", "Brak informacji o plikach do wyświetlenia.")
        return

    print(f"Liczba plików do wyświetlenia: {len(files_info)}")

    # Utworzenie nowego okna dla tabeli
    table_window = tk.Toplevel()
    table_window.title("Informacje o przeniesionych plikach")
    table_window.geometry("1200x600")

    # Utworzenie notebooka (zakładek)
    notebook = ttk.Notebook(table_window)
    notebook.pack(fill="both", expand=True, padx=10, pady=10)

    # Zakładka 1: Podstawowe informacje
    basic_frame = ttk.Frame(notebook)
    notebook.add(basic_frame, text="Podstawowe informacje")

    # Zakładka 2: Zaawansowane informacje
    advanced_frame = ttk.Frame(notebook)
    notebook.add(advanced_frame, text="Zaawansowane informacje")

    # Zakładka 3: Kategorie
    category_frame = ttk.Frame(notebook)
    notebook.add(category_frame, text="Kategorie")

    # Zakładka 4: Grupowanie
    grouping_frame = ttk.Frame(notebook)
    notebook.add(grouping_frame, text="Grupowanie")

    # Utworzenie tabeli z podstawowymi informacjami
    basic_columns = (
        "Nazwa", "Rozszerzenie", "Status", "Czas operacji",
        "Rozmiar", "Data utworzenia", "Data modyfikacji", "Atrybuty"
    )
    basic_tree = ttk.Treeview(basic_frame, columns=basic_columns, show="headings")

    # Definicja nagłówków kolumn
    for col in basic_columns:
        basic_tree.heading(col, text=col)
        basic_tree.column(col, width=120)

    # Dodanie danych do tabeli podstawowych informacji
    print("\nDodawanie danych do tabeli podstawowych informacji:")
    for idx, file_info in enumerate(files_info):
        try:
            # Próba sformatowania rozmiaru
            try:
                formatted_size = format_size(file_info.file_size)
            except Exception as size_error:
                print(f"Błąd formatowania rozmiaru dla {file_info.name}: {size_error}")
                formatted_size = "Błąd"

            values = (
                file_info.name,
                file_info.extension,
                file_info.status,
                file_info.timestamp,
                formatted_size,
                file_info.creation_date,
                file_info.modification_date,
                file_info.attributes
            )

            basic_tree.insert("", "end", values=values)
        except Exception as e:
            print(f"BŁĄD podczas dodawania do tabeli: {e}")
            traceback.print_exc()

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
            advanced_tree.column(col, width=300)
        else:
            advanced_tree.column(col, width=150)

    # Dodanie danych do tabeli zaawansowanych informacji
    for idx, file_info in enumerate(files_info):
        try:
            values = (
                file_info.name,
                file_info.extension,
                file_info.mime_type,
                file_info.file_signature,
                file_info.keywords,
                file_info.headers_info
            )
            advanced_tree.insert("", "end", values=values)
        except Exception as e:
            print(f"BŁĄD podczas dodawania do tabeli zaawansowanej: {e}")
            traceback.print_exc()

    # Dodanie paska przewijania dla zaawansowanej tabeli
    advanced_scrollbar_y = ttk.Scrollbar(advanced_frame, orient="vertical", command=advanced_tree.yview)
    advanced_scrollbar_x = ttk.Scrollbar(advanced_frame, orient="horizontal", command=advanced_tree.xview)
    advanced_tree.configure(yscrollcommand=advanced_scrollbar_y.set, xscrollcommand=advanced_scrollbar_x.set)
    advanced_scrollbar_y.pack(side="right", fill="y")
    advanced_scrollbar_x.pack(side="bottom", fill="x")
    advanced_tree.pack(fill="both", expand=True)

    # Utworzenie tabeli z informacjami o kategoriach
    category_columns = (
        "Nazwa", "Rozszerzenie", "Typ pliku", "Kategoria rozmiaru", "Kategoria daty", "Kategorie z nazwy"
    )
    category_tree = ttk.Treeview(category_frame, columns=category_columns, show="headings")

    # Definicja nagłówków kolumn dla kategorii
    for col in category_columns:
        category_tree.heading(col, text=col)
        if col in ["Kategorie z nazwy"]:
            category_tree.column(col, width=300)
        else:
            category_tree.column(col, width=150)

    # Dodanie danych do tabeli kategorii
    for idx, file_info in enumerate(files_info):
        try:
            # Formatowanie listy kategorii z nazwy
            try:
                name_categories = ", ".join(file_info.category_name) if file_info.category_name else "Brak"
            except Exception as cat_error:
                print(f"Błąd formatowania kategorii z nazwy: {cat_error}")
                name_categories = "Błąd"

            values = (
                file_info.name,
                file_info.extension,
                file_info.category_extension,
                file_info.size_category,
                file_info.date_category,
                name_categories
            )

            category_tree.insert("", "end", values=values)
        except Exception as e:
            print(f"BŁĄD podczas dodawania do tabeli kategorii: {e}")
            traceback.print_exc()

    # Dodanie paska przewijania dla tabeli kategorii
    category_scrollbar_y = ttk.Scrollbar(category_frame, orient="vertical", command=category_tree.yview)
    category_scrollbar_x = ttk.Scrollbar(category_frame, orient="horizontal", command=category_tree.xview)
    category_tree.configure(yscrollcommand=category_scrollbar_y.set, xscrollcommand=category_scrollbar_x.set)
    category_scrollbar_y.pack(side="right", fill="y")
    category_scrollbar_x.pack(side="bottom", fill="x")
    category_tree.pack(fill="both", expand=True)

    # Zakładka grupowania - uproszczona
    print("\nTworzenie zakładki grupowania...")

    # Tworzenie prostego grupowania
    try:
        simple_groups = create_simple_grouping(files_info)

        # Utworzenie widoku drzewa do wyświetlenia grup plików
        group_tree = ttk.Treeview(grouping_frame, show="tree headings")
        group_tree.heading("#0", text="Grupy plików")
        group_tree.column("#0", width=400)

        # Dodanie głównych kategorii grupowania
        extension_node = group_tree.insert("", "end", text="Według rozszerzenia", open=True)
        type_node = group_tree.insert("", "end", text="Według typu pliku", open=True)
        size_node = group_tree.insert("", "end", text="Według rozmiaru", open=True)
        date_node = group_tree.insert("", "end", text="Według daty", open=True)

        # Pomocnicza funkcja do dodawania plików do grupy
        def add_files_to_group(parent_node, category, files):
            try:
                group_node = group_tree.insert(parent_node, "end", text=f"{category} ({len(files)})", open=False)
                for file in files[:10]:  # Pokaż tylko pierwsze 10 plików
                    group_tree.insert(group_node, "end", text=f"{file.name}{file.extension}")
                if len(files) > 10:
                    group_tree.insert(group_node, "end", text=f"... i {len(files) - 10} więcej")
            except Exception as group_error:
                print(f"Błąd dodawania grupy: {group_error}")

        # Wypełnianie drzewa dla każdej kategorii grupowania
        print("Wypełnianie drzewa grupowania:")

        # Według rozszerzenia
        try:
            for category, files in simple_groups['extension'].items():
                add_files_to_group(extension_node, category, files)
        except Exception as ext_error:
            print(f"Błąd dodawania grup według rozszerzenia: {ext_error}")

        # Według typu pliku
        try:
            for category, files in simple_groups['type'].items():
                add_files_to_group(type_node, category, files)
        except Exception as type_error:
            print(f"Błąd dodawania grup według typu: {type_error}")

        # Według rozmiaru
        try:
            for category, files in simple_groups['size'].items():
                add_files_to_group(size_node, category, files)
        except Exception as size_error:
            print(f"Błąd dodawania grup według rozmiaru: {size_error}")

        # Według daty
        try:
            for category, files in simple_groups['date'].items():
                add_files_to_group(date_node, category, files)
        except Exception as date_error:
            print(f"Błąd dodawania grup według daty: {date_error}")

    except Exception as e:
        print(f"BŁĄD podczas tworzenia drzewa grup: {e}")
        traceback.print_exc()
        # Dodaj prostą etykietę w przypadku błędu
        error_label = ttk.Label(grouping_frame, text="Nie udało się wygenerować grup")
        error_label.pack()

    # Dodanie paska przewijania dla drzewa grupowania
    try:
        group_scrollbar_y = ttk.Scrollbar(grouping_frame, orient="vertical", command=group_tree.yview)
        group_scrollbar_x = ttk.Scrollbar(grouping_frame, orient="horizontal", command=group_tree.xview)
        group_tree.configure(yscrollcommand=group_scrollbar_y.set, xscrollcommand=group_scrollbar_x.set)
        group_scrollbar_y.pack(side="right", fill="y")
        group_scrollbar_x.pack(side="bottom", fill="x")
        group_tree.pack(fill="both", expand=True)
    except:
        print("Błąd podczas dodawania pasków przewijania")

    # Przycisk do eksportu danych
    export_button = tk.Button(
        table_window,
        text="Eksportuj do pliku CSV",
        command=lambda: export_to_csv(files_info)
    )
    export_button.pack(pady=10)

    print("Zakończono tworzenie interfejsu tabeli plików")


def create_simple_grouping(files_info):
    """Tworzy proste grupowanie plików"""
    from collections import defaultdict

    groups = {
        'extension': defaultdict(list),
        'type': defaultdict(list),
        'size': defaultdict(list),
        'date': defaultdict(list)
    }

    for file_info in files_info:
        # Według rozszerzenia
        ext = file_info.extension.lower() if file_info.extension else "(brak)"
        groups['extension'][ext].append(file_info)

        # Według typu pliku
        groups['type'][file_info.category_extension].append(file_info)

        # Według rozmiaru
        groups['size'][file_info.size_category].append(file_info)

        # Według daty
        groups['date'][file_info.date_category].append(file_info)

    return groups