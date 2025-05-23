# main.py - Uproszczony główny plik aplikacji
import tkinter as tk
from tkinter import messagebox
import sys
import os
from pathlib import Path

# Dodaj katalog główny do ścieżki Python
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

# Importy modułów
from models import FileInfo
from category_analyzer import CategoryAnalyzer
from file_operations import FileOperations
from gui_components import MainWindow, ResultsWindow, ProgressDialog
from data_export import show_export_dialog


class FileOrganizerApp:
    """Główna klasa aplikacji organizatora plików"""

    def __init__(self):
        self.categorizer = CategoryAnalyzer()
        self.file_ops = FileOperations(self.categorizer)
        self.files_info = []

        # Główne okno
        self.main_window = MainWindow(self.start_organization_process)

    def start_organization_process(self):
        """Rozpoczyna proces organizacji plików"""
        try:
            # 1. Wybór plików
            files = self.file_ops.select_files()
            if not files:
                messagebox.showinfo("Informacja", "Nie wybrano żadnych plików.")
                return

            print(f"Wybrano {len(files)} plików do organizacji")

            # 2. Sprawdź sugestie automatyczne
            suggestions = self.file_ops.get_smart_suggestions(files)
            destination = None

            if suggestions:
                # Pokaż sugestie użytkownikowi
                suggestion_message = self._format_suggestions(suggestions)
                response = messagebox.askyesno(
                    "Inteligentne Sugestie",
                    f"System znalazł następujące sugestie:\n\n{suggestion_message}\n\n"
                    "Czy chcesz użyć pierwszej sugestii?"
                )

                if response:
                    destination = list(suggestions.keys())[0]

            # 3. Jeśli brak sugestii lub użytkownik odmówił, wybierz ręcznie
            if not destination:
                destination = self.file_ops.select_destination()
                if not destination:
                    messagebox.showinfo("Informacja", "Nie wybrano folderu docelowego.")
                    return

            print(f"Wybrano folder docelowy: {destination}")

            # 4. Pokaż okno postępu
            progress = ProgressDialog(self.main_window.root, "Organizacja Plików")
            progress.update_status("Analizowanie plików...")

            try:
                # 5. Przenieś pliki
                self.files_info = self.file_ops.move_files(files, destination)

                progress.update_status("Operacja zakończona!")
                progress.close()

                # 6. Pokaż wyniki
                self._show_results()

            except Exception as e:
                progress.close()
                raise e

        except Exception as e:
            print(f"Błąd podczas organizacji plików: {e}")
            messagebox.showerror("Błąd", f"Wystąpił błąd:\n{str(e)}")

    def _format_suggestions(self, suggestions: dict) -> str:
        """Formatuje sugestie do wyświetlenia"""
        message_parts = []
        for destination, files in list(suggestions.items())[:3]:  # Maksymalnie 3 sugestie
            files_list = ", ".join(files[:3])  # Maksymalnie 3 nazwy plików
            if len(files) > 3:
                files_list += f" i {len(files) - 3} więcej"

            message_parts.append(f"📁 {destination}\n   Pliki: {files_list}")

        return "\n\n".join(message_parts)

    def _show_results(self):
        """Wyświetla wyniki operacji"""
        # Statystyki operacji
        total = len(self.files_info)
        success = len([f for f in self.files_info if f.status == "success"])
        errors = len([f for f in self.files_info if f.status.startswith("error")])
        skipped = len([f for f in self.files_info if f.status == "skipped"])

        # Pokaż podsumowanie
        if errors > 0:
            messagebox.showwarning(
                "Ostrzeżenie",
                f"Organizacja zakończona z ostrzeżeniami:\n\n"
                f"✅ Pomyślne: {success}/{total}\n"
                f"❌ Błędy: {errors}\n"
                f"⏩ Pominięte: {skipped}"
            )
        else:
            messagebox.showinfo(
                "Sukces",
                f"Organizacja plików zakończona pomyślnie!\n\n"
                f"✅ Przeniesiono: {success}/{total} plików\n"
                f"⏩ Pominięto: {skipped} plików"
            )

        # Otwórz okno wyników
        ResultsWindow(self.main_window.root, self.files_info)

    def run(self):
        """Uruchamia aplikację"""
        try:
            print("🚀 Uruchamianie Organizatora Plików...")
            print(f"📁 Katalog roboczy: {current_dir}")
            print(f"💾 Historia plików: {self.categorizer.history_file}")

            # Pokaż statystyki historii
            stats = self.categorizer.get_category_stats()
            if stats:
                print("📊 Statystyki historii:")
                for category, count in stats.items():
                    print(f"   {category}: {count} plików")
            else:
                print("📊 Brak historii - to pierwszy start aplikacji")

            # Uruchom GUI
            self.main_window.run()

        except Exception as e:
            print(f"Krytyczny błąd aplikacji: {e}")
            messagebox.showerror("Błąd Krytyczny", f"Wystąpił krytyczny błąd:\n{str(e)}")


class ConfigManager:
    """Prosty menedżer konfiguracji aplikacji"""

    DEFAULT_CONFIG = {
        "history_file": "transfer_history.json",
        "auto_suggestions": True,
        "confirm_overwrites": True,
        "create_backups": False,
        "log_operations": True
    }

    def __init__(self, config_file: str = "app_config.json"):
        self.config_file = config_file
        self.config = self.load_config()

    def load_config(self) -> dict:
        """Wczytuje konfigurację z pliku"""
        try:
            if Path(self.config_file).exists():
                import json
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)

                # Połącz z domyślną konfiguracją
                config = self.DEFAULT_CONFIG.copy()
                config.update(loaded_config)
                return config

        except Exception as e:
            print(f"Błąd wczytywania konfiguracji: {e}")

        return self.DEFAULT_CONFIG.copy()

    def save_config(self):
        """Zapisuje konfigurację do pliku"""
        try:
            import json
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Błąd zapisywania konfiguracji: {e}")

    def get(self, key: str, default=None):
        """Pobiera wartość z konfiguracji"""
        return self.config.get(key, default)

    def set(self, key: str, value):
        """Ustawia wartość w konfiguracji"""
        self.config[key] = value
        self.save_config()


def check_dependencies():
    """Sprawdza czy wszystkie wymagane moduły są dostępne"""
    missing_modules = []

    # Sprawdź podstawowe moduły
    required_modules = ['tkinter', 'pathlib', 'json', 'csv']

    for module in required_modules:
        try:
            __import__(module)
        except ImportError:
            missing_modules.append(module)

    if missing_modules:
        print(f"❌ Brakujące moduły: {', '.join(missing_modules)}")
        return False

    print("✅ Wszystkie wymagane moduły są dostępne")
    return True


def main():
    """Główna funkcja aplikacji"""
    try:
        print("=" * 50)
        print("    ORGANIZATOR PLIKÓW - UPROSZCZONA WERSJA")
        print("=" * 50)

        # Sprawdź zależności
        if not check_dependencies():
            input("Naciśnij Enter aby zakończyć...")
            return

        # Utwórz i uruchom aplikację
        app = FileOrganizerApp()
        app.run()

    except KeyboardInterrupt:
        print("\n👋 Aplikacja została przerwana przez użytkownika")
    except Exception as e:
        print(f"\n💥 Krytyczny błąd aplikacji: {e}")
        import traceback
        traceback.print_exc()

        # Pokaż dialog błędu jeśli tkinter jest dostępne
        try:
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror(
                "Krytyczny Błąd",
                f"Aplikacja napotkała krytyczny błąd:\n\n{str(e)}\n\n"
                "Sprawdź konsolę aby uzyskać więcej szczegółów."
            )
        except:
            pass

    print("\n👋 Dziękujemy za korzystanie z Organizatora Plików!")


if __name__ == "__main__":
    main()