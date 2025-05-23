# data_export.py - Uproszczony eksport danych
import csv
import json
from pathlib import Path
from typing import List
from tkinter import filedialog, messagebox
from models import FileInfo


class DataExporter:
    """Klasa do eksportu danych o plikach"""

    @staticmethod
    def export_to_csv(files_info: List[FileInfo], filename: str = None) -> bool:
        """Eksportuje dane do pliku CSV"""
        if not filename:
            filename = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
                title="Zapisz dane jako CSV"
            )

        if not filename:
            return False

        try:
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)

                # Nagłówki
                headers = [
                    'Nazwa', 'Rozszerzenie', 'Kategoria', 'Rozmiar (bajty)',
                    'Rozmiar (czytelny)', 'Status', 'Ścieżka źródłowa',
                    'Ścieżka docelowa', 'Data utworzenia', 'Data modyfikacji',
                    'Typ MIME', 'Słowa kluczowe', 'Czas operacji'
                ]
                writer.writerow(headers)

                # Dane
                for file_info in files_info:
                    row = [
                        file_info.name,
                        file_info.extension,
                        file_info.category,
                        file_info.size,
                        file_info.display_size,
                        file_info.status,
                        file_info.source_path,
                        file_info.destination_path,
                        file_info.creation_date,
                        file_info.modification_date,
                        file_info.mime_type,
                        file_info.keywords,
                        file_info.timestamp
                    ]
                    writer.writerow(row)

            messagebox.showinfo("Sukces", f"Dane wyeksportowane do:\n{filename}")
            return True

        except Exception as e:
            messagebox.showerror("Błąd", f"Nie udało się wyeksportować danych:\n{str(e)}")
            return False

    @staticmethod
    def export_to_json(files_info: List[FileInfo], filename: str = None) -> bool:
        """Eksportuje dane do pliku JSON"""
        if not filename:
            filename = filedialog.asksaveasfilename(
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
                title="Zapisz dane jako JSON"
            )

        if not filename:
            return False

        try:
            # Konwertuj FileInfo na słowniki
            data = []
            for file_info in files_info:
                file_dict = {
                    'name': file_info.name,
                    'extension': file_info.extension,
                    'category': file_info.category,
                    'size': file_info.size,
                    'display_size': file_info.display_size,
                    'status': file_info.status,
                    'source_path': file_info.source_path,
                    'destination_path': file_info.destination_path,
                    'creation_date': file_info.creation_date,
                    'modification_date': file_info.modification_date,
                    'mime_type': file_info.mime_type,
                    'keywords': file_info.keywords,
                    'timestamp': file_info.timestamp
                }
                data.append(file_dict)

            # Zapisz do pliku
            with open(filename, 'w', encoding='utf-8') as jsonfile:
                json.dump(data, jsonfile, ensure_ascii=False, indent=2)

            messagebox.showinfo("Sukces", f"Dane wyeksportowane do:\n{filename}")
            return True

        except Exception as e:
            messagebox.showerror("Błąd", f"Nie udało się wyeksportować danych:\n{str(e)}")
            return False

    @staticmethod
    def export_summary_report(files_info: List[FileInfo], filename: str = None) -> bool:
        """Eksportuje raport podsumowujący"""
        if not filename:
            filename = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
                title="Zapisz raport podsumowujący"
            )

        if not filename:
            return False

        try:
            from collections import Counter

            # Przygotuj statystyki
            total_files = len(files_info)
            total_size = sum(f.size for f in files_info)
            categories = Counter(f.category for f in files_info)
            extensions = Counter(f.extension for f in files_info)
            statuses = Counter(f.status for f in files_info)

            # Formatuj rozmiar
            if total_size > 1024 ** 3:
                size_str = f"{total_size / (1024 ** 3):.2f} GB"
            elif total_size > 1024 ** 2:
                size_str = f"{total_size / (1024 ** 2):.2f} MB"
            else:
                size_str = f"{total_size / 1024:.2f} KB"

            # Utwórz raport
            report = f"""RAPORT ORGANIZACJI PLIKÓW
{'=' * 50}

PODSUMOWANIE:
- Całkowita liczba plików: {total_files}
- Łączny rozmiar: {size_str} ({total_size:,} bajtów)
- Data raportu: {files_info[0].timestamp if files_info else 'N/A'}

STATYSTYKI KATEGORII:
{'-' * 30}
"""

            for category, count in categories.most_common():
                percentage = (count / total_files) * 100
                report += f"- {category:15}: {count:4} plików ({percentage:5.1f}%)\n"

            report += f"""
NAJCZĘSTSZE ROZSZERZENIA:
{'-' * 30}
"""

            for ext, count in extensions.most_common(10):
                display_ext = ext if ext else "(brak)"
                percentage = (count / total_files) * 100
                report += f"- {display_ext:10}: {count:4} plików ({percentage:5.1f}%)\n"

            report += f"""
WYNIKI OPERACJI:
{'-' * 30}
"""

            for status, count in statuses.items():
                percentage = (count / total_files) * 100
                report += f"- {status:15}: {count:4} plików ({percentage:5.1f}%)\n"

            # Zapisz raport
            with open(filename, 'w', encoding='utf-8') as txtfile:
                txtfile.write(report)

            messagebox.showinfo("Sukces", f"Raport zapisany do:\n{filename}")
            return True

        except Exception as e:
            messagebox.showerror("Błąd", f"Nie udało się utworzyć raportu:\n{str(e)}")
            return False

    @staticmethod
    def quick_backup_data(files_info: List[FileInfo]) -> bool:
        """Szybka kopia zapasowa danych"""
        try:
            from datetime import datetime

            # Nazwa pliku z timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"file_organizer_backup_{timestamp}.json"

            # Zapisz w katalogu roboczym
            return DataExporter.export_to_json(files_info, backup_filename)

        except Exception as e:
            messagebox.showerror("Błąd", f"Nie udało się utworzyć kopii zapasowej:\n{str(e)}")
            return False


# Funkcje pomocnicze dla kompatybilności z oryginalnym kodem
def export_to_csv(files_info: List[FileInfo]):
    """Funkcja pomocnicza - eksport do CSV"""
    return DataExporter.export_to_csv(files_info)


def export_to_json(files_info: List[FileInfo]):
    """Funkcja pomocnicza - eksport do JSON"""
    return DataExporter.export_to_json(files_info)


def create_summary_report(files_info: List[FileInfo]):
    """Funkcja pomocnicza - tworzenie raportu"""
    return DataExporter.export_summary_report(files_info)


class ExportDialog:
    """Dialog wyboru formatu eksportu"""

    def __init__(self, parent, files_info: List[FileInfo]):
        self.parent = parent
        self.files_info = files_info
        self.result = None
        self.create_dialog()

    def create_dialog(self):
        """Tworzy dialog wyboru eksportu"""
        import tkinter as tk
        from tkinter import ttk

        self.center_window(350, 200)

        # Okno dialogowe
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("Eksport Danych")
        self.dialog.geometry("350x200")
        self.dialog.resizable(False, False)
        self.dialog.transient(self.parent)
        self.dialog.grab_set()

        # Wyśrodkuj okno
        self.dialog.eval('tk::PlaceWindow . center')

        # Główna ramka
        main_frame = ttk.Frame(self.dialog, padding="20")
        main_frame.pack(fill="both", expand=True)

        # Tytuł
        title_label = ttk.Label(main_frame, text="Wybierz format eksportu:", font=("Arial", 11, "bold"))
        title_label.pack(pady=(0, 15))

        # Opcje eksportu
        self.export_format = tk.StringVar(value="csv")

        formats = [
            ("CSV (arkusz kalkulacyjny)", "csv"),
            ("JSON (dane strukturalne)", "json"),
            ("TXT (raport tekstowy)", "txt")
        ]

        for text, value in formats:
            ttk.Radiobutton(
                main_frame,
                text=text,
                value=value,
                variable=self.export_format
            ).pack(anchor="w", pady=2)

        # Przyciski
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.pack(fill="x", pady=(20, 0))

        ttk.Button(
            buttons_frame,
            text="Eksportuj",
            command=self.export_data
        ).pack(side="left")

        ttk.Button(
            buttons_frame,
            text="Anuluj",
            command=self.dialog.destroy
        ).pack(side="right")

    def center_window(self, width=350, height=200):
        self.dialog.update_idletasks()
        screen_width = self.dialog.winfo_screenwidth()
        screen_height = self.dialog.winfo_screenheight()
        x = (screen_width // 2) - (width // 2)
        y = (screen_height // 2) - (height // 2)
        self.dialog.geometry(f"{width}x{height}+{x}+{y}")

    def export_data(self):
        """Eksportuje dane w wybranym formacie"""
        format_type = self.export_format.get()

        if format_type == "csv":
            success = DataExporter.export_to_csv(self.files_info)
        elif format_type == "json":
            success = DataExporter.export_to_json(self.files_info)
        elif format_type == "txt":
            success = DataExporter.export_summary_report(self.files_info)
        else:
            success = False

        if success:
            self.dialog.destroy()


def show_export_dialog(parent, files_info: List[FileInfo]):
    """Wyświetla dialog eksportu"""
    ExportDialog(parent, files_info)


