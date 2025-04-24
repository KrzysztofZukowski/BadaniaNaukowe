# data_export.py
import tkinter as tk
from tkinter import filedialog, messagebox


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
                    "Typ MIME,Sygnatura pliku,Słowa kluczowe,Informacje o nagłówkach\n")

            # Dane
            for file_info in files_info:
                # Uciekanie cudzysłowów w polach, aby uniknąć problemów z CSV
                keywords = file_info.keywords.replace('"', '""')
                headers_info = file_info.headers_info.replace('"', '""')

                f.write(
                    f'"{file_info.name}","{file_info.extension}","{file_info.source_path}",' +
                    f'"{file_info.destination_path}","{file_info.status}","{file_info.timestamp}",' +
                    f'"{file_info.file_size}","{file_info.creation_date}","{file_info.modification_date}",' +
                    f'"{file_info.attributes}",' +
                    f'"{file_info.mime_type}","{file_info.file_signature}","{keywords}","{headers_info}"\n'
                )

        messagebox.showinfo("Sukces", f"Dane zostały pomyślnie wyeksportowane do {file_path}")
    except Exception as e:
        messagebox.showerror("Błąd", f"Wystąpił błąd podczas eksportu danych: {e}")