
import tkinter as tk
from tkinter import filedialog, messagebox
import json


def export_to_csv(files_info):
    """Funkcja eksportująca informacje o plikach do pliku CSV"""
    file_path = filedialog.asksaveasfilename(
        defaultextension=".csv",
        filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
        title="Zapisz informacje o plikach"
    )

    if not file_path:
        return

    try:
        with open(file_path, "w", encoding="utf-8") as f:
            # Nagłówki
            f.write("Nazwa,Rozszerzenie,Ścieżka źródłowa,Ścieżka docelowa,Status,Czas operacji," +
                    "Rozmiar (bajty),Data utworzenia,Data modyfikacji,Atrybuty," +
                    "Typ MIME,Sygnatura pliku,Słowa kluczowe,Informacje o nagłówkach," +
                    "Kategoria pliku,Kategorie z nazwy,Sugerowane lokalizacje," +
                    "Kategoria rozmiaru,Kategoria daty,Kategorie przedmiotów,Kategorie czasowe,Wszystkie kategorie\n")

            # Dane
            for file_info in files_info:
                # Przygotowanie danych
                keywords = file_info.keywords.replace('"', '""')
                headers_info = file_info.headers_info.replace('"', '""')

                # Konwersja list i słowników na format tekstowy
                name_categories = "|".join(file_info.category_name) if file_info.category_name else ""
                subject_categories = "|".join(file_info.subject_categories) if file_info.subject_categories else ""
                time_pattern_categories = "|".join(file_info.time_pattern_categories) if file_info.time_pattern_categories else ""
                all_categories = "|".join(file_info.all_categories) if file_info.all_categories else ""

                suggested_locs = []
                for loc, reason, count in file_info.suggested_locations:
                    suggested_locs.append(f"{loc}:{reason}:{count}")
                suggested_locations_str = "|".join(suggested_locs)

                f.write(
                    f'"{file_info.name}","{file_info.extension}","{file_info.source_path}",' +
                    f'"{file_info.destination_path}","{file_info.status}","{file_info.timestamp}",' +
                    f'"{file_info.file_size}","{file_info.creation_date}","{file_info.modification_date}",' +
                    f'"{file_info.attributes}",' +
                    f'"{file_info.mime_type}","{file_info.file_signature}","{keywords}","{headers_info}",' +
                    f'"{file_info.category_extension}","{name_categories}","{suggested_locations_str}",' +
                    f'"{file_info.size_category}","{file_info.date_category}","{subject_categories}",' +
                    f'"{time_pattern_categories}","{all_categories}"\n'
                )

        messagebox.showinfo("Sukces", f"Dane zostały pomyślnie wyeksportowane do {file_path}")
    except Exception as e:
        messagebox.showerror("Błąd", f"Wystąpił błąd podczas eksportu danych: {e}")