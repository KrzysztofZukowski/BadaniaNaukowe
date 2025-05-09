# gui_components.py
import tkinter as tk
from tkinter import ttk, messagebox

from data_export import export_to_csv


# gui_components.py - dodaj import na początku pliku
from file_size_reader import FileSizeReader

# Zastąp istniejącą funkcję format_size
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


def show_files_table(files_info, category_analyzer):
    """Funkcja wyświetlająca tabelę z informacjami o przeniesionych plikach"""
    import traceback

    print("\n=== Wyświetlanie tabeli plików ===")

    if not files_info:
        print("Brak informacji o plikach do wyświetlenia.")
        messagebox.showinfo("Informacja", "Brak informacji o plikach do wyświetlenia.")
        return

    print(f"Liczba plików do wyświetlenia: {len(files_info)}")

    # Wydrukuj szczegóły wszystkich plików dla diagnostyki
    for idx, file_info in enumerate(files_info):
        print(f"\nPlik {idx + 1}: {file_info.name}{file_info.extension}")
        print(f"  Status: {file_info.status}")
        print(f"  Czas operacji: {file_info.timestamp}")
        print(f"  Rozmiar surowy: {file_info.file_size} typu {type(file_info.file_size)}")

        # Próba sformatowania rozmiaru
        try:
            formatted_size = format_size(file_info.file_size)
            print(f"  Rozmiar sformatowany: {formatted_size}")
        except Exception as e:
            print(f"  BŁĄD formatowania rozmiaru: {e}")
            traceback.print_exc()

        print(f"  Data utworzenia: {file_info.creation_date}")
        print(f"  Data modyfikacji: {file_info.modification_date}")
        print(f"  Kategoria rozszerzenia: {file_info.category_extension}")
        print(f"  Kategorie z nazwy: {file_info.category_name}")

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

    # Zakładka 3: Kategoryzacja
    category_frame = ttk.Frame(notebook)
    notebook.add(category_frame, text="Kategoryzacja")

    # Zakładka 4: Nowe kategorie
    new_categories_frame = ttk.Frame(notebook)
    notebook.add(new_categories_frame, text="Nowe kategorie")

    # Zakładka 5: Grupowanie plików
    grouping_frame = ttk.Frame(notebook)
    notebook.add(grouping_frame, text="Grupowanie plików")

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
    print("\nDodawanie danych do tabeli podstawowych informacji:")
    for idx, file_info in enumerate(files_info):
        try:
            # Próba sformatowania rozmiaru
            try:
                formatted_size = format_size(file_info.file_size)
            except Exception as size_error:
                print(f"Błąd formatowania rozmiaru dla {file_info.name}: {size_error}")
                formatted_size = "Błąd"

            print(
                f"Dodawanie pliku {idx + 1} do tabeli: {file_info.name}{file_info.extension}, rozmiar={formatted_size}")

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

            # Wydrukuj wszystkie wartości do dodania
            for i, col in enumerate(basic_columns):
                print(f"  {col}: {values[i]}")

            basic_tree.insert("", "end", values=values)
            print(f"  Dodano pomyślnie")
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
            advanced_tree.column(col, width=300)  # Szersze kolumny dla dłuższych tekstów
        else:
            advanced_tree.column(col, width=150)

    # Dodanie danych do tabeli zaawansowanych informacji
    print("\nDodawanie danych do tabeli zaawansowanych informacji:")
    for idx, file_info in enumerate(files_info):
        try:
            print(f"Dodawanie pliku {idx + 1} do tabeli zaawansowanej: {file_info.name}{file_info.extension}")

            values = (
                file_info.name,
                file_info.extension,
                file_info.mime_type,
                file_info.file_signature,
                file_info.keywords,
                file_info.headers_info
            )

            advanced_tree.insert("", "end", values=values)
            print(f"  Dodano pomyślnie")
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

    # Utworzenie tabeli z informacjami o kategoryzacji
    category_columns = (
        "Nazwa", "Rozszerzenie", "Kategoria pliku", "Kategorie z nazwy", "Sugerowane lokalizacje"
    )
    category_tree = ttk.Treeview(category_frame, columns=category_columns, show="headings")

    # Definicja nagłówków kolumn dla kategoryzacji
    for col in category_columns:
        category_tree.heading(col, text=col)
        if col in ["Sugerowane lokalizacje"]:
            category_tree.column(col, width=400)  # Szersze kolumny dla dłuższych tekstów
        elif col in ["Kategorie z nazwy"]:
            category_tree.column(col, width=200)
        else:
            category_tree.column(col, width=150)

    # Dodanie danych do tabeli kategoryzacji
    print("\nDodawanie danych do tabeli kategoryzacji:")
    for idx, file_info in enumerate(files_info):
        try:
            print(f"Dodawanie pliku {idx + 1} do tabeli kategoryzacji: {file_info.name}{file_info.extension}")

            # Formatowanie listy kategorii z nazwy
            try:
                name_categories = ", ".join(file_info.category_name) if file_info.category_name else "Brak"
            except Exception as cat_error:
                print(f"Błąd formatowania kategorii z nazwy: {cat_error}")
                name_categories = "Błąd"

            # Formatowanie sugerowanych lokalizacji
            try:
                suggested_locs = []
                for loc, reason, count in file_info.suggested_locations:
                    suggested_locs.append(f"{loc} ({reason}, {count} razy)")
                suggested_locations_str = "\n".join(suggested_locs) if suggested_locs else "Brak sugestii"
            except Exception as loc_error:
                print(f"Błąd formatowania sugerowanych lokalizacji: {loc_error}")
                suggested_locations_str = "Błąd"

            values = (
                file_info.name,
                file_info.extension,
                file_info.category_extension,
                name_categories,
                suggested_locations_str
            )

            category_tree.insert("", "end", values=values)
            print(f"  Dodano pomyślnie")
        except Exception as e:
            print(f"BŁĄD podczas dodawania do tabeli kategoryzacji: {e}")
            traceback.print_exc()

    # Dodanie paska przewijania dla tabeli kategoryzacji
    category_scrollbar_y = ttk.Scrollbar(category_frame, orient="vertical", command=category_tree.yview)
    category_scrollbar_x = ttk.Scrollbar(category_frame, orient="horizontal", command=category_tree.xview)
    category_tree.configure(yscrollcommand=category_scrollbar_y.set, xscrollcommand=category_scrollbar_x.set)
    category_scrollbar_y.pack(side="right", fill="y")
    category_scrollbar_x.pack(side="bottom", fill="x")
    category_tree.pack(fill="both", expand=True)

    # Utworzenie tabeli z nowymi kategoriami
    new_cat_columns = (
        "Nazwa", "Rozszerzenie", "Rozmiar", "Kategoria rozmiaru", "Kategoria daty",
        "Kategorie przedmiotów", "Kategorie czasowe", "Wszystkie kategorie"
    )
    new_cat_tree = ttk.Treeview(new_categories_frame, columns=new_cat_columns, show="headings")

    # Definicja nagłówków kolumn dla nowych kategorii
    for col in new_cat_columns:
        new_cat_tree.heading(col, text=col)
        if col in ["Wszystkie kategorie", "Kategorie czasowe", "Kategorie przedmiotów"]:
            new_cat_tree.column(col, width=300)  # Szersze kolumny dla dłuższych tekstów
        else:
            new_cat_tree.column(col, width=150)

    # Dodanie danych do tabeli nowych kategorii
    print("\nDodawanie danych do tabeli nowych kategorii:")
    for idx, file_info in enumerate(files_info):
        try:
            print(f"Dodawanie pliku {idx + 1} do tabeli nowych kategorii: {file_info.name}{file_info.extension}")

            # Formatowanie list kategorii
            try:
                subject_cats = ", ".join(file_info.subject_categories) if file_info.subject_categories else "Brak"
                time_pattern_cats = ", ".join(
                    file_info.time_pattern_categories) if file_info.time_pattern_categories else "Brak"
                all_cats = ", ".join(file_info.all_categories) if file_info.all_categories else "Brak"
            except Exception as cats_error:
                print(f"Błąd formatowania kategorii: {cats_error}")
                subject_cats = "Błąd"
                time_pattern_cats = "Błąd"
                all_cats = "Błąd"

            # Próba sformatowania rozmiaru
            try:
                formatted_size = format_size(file_info.file_size)
            except Exception as size_error:
                print(f"Błąd formatowania rozmiaru dla {file_info.name}: {size_error}")
                formatted_size = "Błąd"

            values = (
                file_info.name,
                file_info.extension,
                formatted_size,
                file_info.size_category,
                file_info.date_category,
                subject_cats,
                time_pattern_cats,
                all_cats
            )

            new_cat_tree.insert("", "end", values=values)
            print(f"  Dodano pomyślnie")
        except Exception as e:
            print(f"BŁĄD podczas dodawania do tabeli nowych kategorii: {e}")
            traceback.print_exc()

    # Dodanie paska przewijania dla tabeli nowych kategorii
    new_cat_scrollbar_y = ttk.Scrollbar(new_categories_frame, orient="vertical", command=new_cat_tree.yview)
    new_cat_scrollbar_x = ttk.Scrollbar(new_categories_frame, orient="horizontal", command=new_cat_tree.xview)
    new_cat_tree.configure(yscrollcommand=new_cat_scrollbar_y.set, xscrollcommand=new_cat_scrollbar_x.set)
    new_cat_scrollbar_y.pack(side="right", fill="y")
    new_cat_scrollbar_x.pack(side="bottom", fill="x")
    new_cat_tree.pack(fill="both", expand=True)

    # Wywołanie metody grupowania plików
    print("\nGrupowanie plików...")
    try:
        grouped_files = category_analyzer.group_files_by_category(files_info)
        print(f"Grupowanie zakończone pomyślnie. Liczba grup: {sum(len(g) for g in grouped_files.values())}")
    except Exception as group_error:
        print(f"BŁĄD podczas grupowania plików: {group_error}")
        traceback.print_exc()
        # Stwórz pustą strukturę w przypadku błędu
        grouped_files = {
            'według_rozszerzenia': {},
            'według_nazwy': {},
            'według_rozmiaru': {},
            'według_wieku': {},
            'według_przedmiotu': {},
            'według_wzorca_czasowego': {}
        }

    # Utworzenie widoku drzewa do wyświetlenia grup plików
    group_tree = ttk.Treeview(grouping_frame, show="tree headings")
    group_tree.heading("#0", text="Kategorie grupowania")
    group_tree.column("#0", width=300)

    # Dodanie głównych kategorii grupowania
    try:
        extension_node = group_tree.insert("", "end", text="Według rozszerzenia", open=True)
        name_node = group_tree.insert("", "end", text="Według nazwy", open=True)
        size_node = group_tree.insert("", "end", text="Według rozmiaru", open=True)
        age_node = group_tree.insert("", "end", text="Według wieku", open=True)
        subject_node = group_tree.insert("", "end", text="Według przedmiotu", open=True)
        time_node = group_tree.insert("", "end", text="Według wzorca czasowego", open=True)

        # Pomocnicza funkcja do dodawania plików do grupy
        def add_files_to_group(parent_node, category, files):
            try:
                print(f"Dodawanie grupy: {category} z {len(files)} plikami")
                group_node = group_tree.insert(parent_node, "end", text=f"{category} ({len(files)})", open=False)
                for file in files:
                    try:
                        file_node = group_tree.insert(group_node, "end", text=f"{file.name}{file.extension}")
                    except Exception as file_error:
                        print(f"Błąd dodawania pliku do grupy: {file_error}")
            except Exception as group_error:
                print(f"Błąd dodawania grupy: {group_error}")

        # Wypełnianie drzewa dla każdej kategorii grupowania
        print("\nWypełnianie drzewa grupowania:")

        # Według rozszerzenia
        try:
            print("Dodawanie grup według rozszerzenia")
            for category, files in grouped_files['według_rozszerzenia'].items():
                add_files_to_group(extension_node, category, files)
        except Exception as ext_error:
            print(f"Błąd dodawania grup według rozszerzenia: {ext_error}")

        # Według nazwy
        try:
            print("Dodawanie grup według nazwy")
            for category, files in grouped_files['według_nazwy'].items():
                add_files_to_group(name_node, category, files)
        except Exception as name_error:
            print(f"Błąd dodawania grup według nazwy: {name_error}")

        # Według rozmiaru
        try:
            print("Dodawanie grup według rozmiaru")
            for category, files in grouped_files['według_rozmiaru'].items():
                add_files_to_group(size_node, category, files)
        except Exception as size_error:
            print(f"Błąd dodawania grup według rozmiaru: {size_error}")

        # Według wieku
        try:
            print("Dodawanie grup według wieku")
            for category, files in grouped_files['według_wieku'].items():
                add_files_to_group(age_node, category, files)
        except Exception as age_error:
            print(f"Błąd dodawania grup według wieku: {age_error}")

        # Według przedmiotu
        try:
            print("Dodawanie grup według przedmiotu")
            for category, files in grouped_files['według_przedmiotu'].items():
                add_files_to_group(subject_node, category, files)
        except Exception as subject_error:
            print(f"Błąd dodawania grup według przedmiotu: {subject_error}")

        # Według wzorca czasowego
        try:
            print("Dodawanie grup według wzorca czasowego")
            for category, files in grouped_files['według_wzorca_czasowego'].items():
                add_files_to_group(time_node, category, files)
        except Exception as time_error:
            print(f"Błąd dodawania grup według wzorca czasowego: {time_error}")

    except Exception as e:
        print(f"BŁĄD podczas tworzenia drzewa grup: {e}")
        traceback.print_exc()

    # Dodanie paska przewijania dla drzewa grupowania
    group_scrollbar_y = ttk.Scrollbar(grouping_frame, orient="vertical", command=group_tree.yview)
    group_scrollbar_x = ttk.Scrollbar(grouping_frame, orient="horizontal", command=group_tree.xview)
    group_tree.configure(yscrollcommand=group_scrollbar_y.set, xscrollcommand=group_scrollbar_x.set)
    group_scrollbar_y.pack(side="right", fill="y")
    group_scrollbar_x.pack(side="bottom", fill="x")
    group_tree.pack(fill="both", expand=True)

    # Przycisk do eksportu danych
    export_button = tk.Button(
        table_window,
        text="Eksportuj do pliku CSV",
        command=lambda: export_to_csv(files_info)
    )
    export_button.pack(pady=10)

    print("Zakończono tworzenie interfejsu tabeli plików")