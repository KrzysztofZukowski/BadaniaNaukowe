# main.py
import tkinter as tk
from tkinter import messagebox
import os
import sys

# Upewniamy się, że katalog z naszymi modułami jest w ścieżce Pythona
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

# Importujemy nasze moduły
from file_operations import select_files, select_destination, move_files
from gui_components import create_main_window, setup_ui, show_files_table
from models import FileInfo
# Możemy też zaimportować nowy moduł, nawet jeśli nie używamy go bezpośrednio w main.py
# jest to dobra praktyka, by upewnić się, że moduł jest dostępny
import file_analyzer


def main():
    """Główna funkcja programu"""
    # Utworzenie głównego okna
    root = create_main_window()

    # Zmienna do przechowywania informacji o plikach
    files_info_list = []

    # Funkcja do obsługi procesu przenoszenia
    def start_moving_process():
        nonlocal files_info_list

        files = select_files()
        if not files:
            messagebox.showinfo("Informacja", "Nie wybrano żadnych plików.")
            return

        destination = select_destination()
        if not destination:
            messagebox.showinfo("Informacja", "Nie wybrano folderu docelowego.")
            return

        files_info_list = move_files(files, destination)

        # Liczenie statystyk
        success_count = len([f for f in files_info_list if f.status == "Przeniesiono"])
        failed_count = len(files_info_list) - success_count

        if failed_count > 0:
            messagebox.showwarning(
                "Uwaga",
                f"Przeniesiono {success_count} z {len(files_info_list)} plików.\n"
                f"Nie udało się przenieść {failed_count} plików."
            )
        else:
            messagebox.showinfo(
                "Sukces",
                f"Wszystkie pliki ({success_count}) zostały pomyślnie przeniesione do: {destination}"
            )

        # Wyświetlenie tabeli z informacjami o plikach
        show_files_table(files_info_list)

    # Konfiguracja interfejsu użytkownika
    setup_ui(root, start_moving_process)

    # Uruchomienie głównej pętli aplikacji
    root.mainloop()


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Wystąpił błąd: {e}")
        import traceback

        traceback.print_exc()