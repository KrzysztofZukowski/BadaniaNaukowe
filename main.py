import tkinter as tk
from tkinter import messagebox
import os
import sys

# Upewniamy się, że katalog z naszymi modułami jest w ścieżce Pythona
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

# Importujemy funkcje bezpośrednio
from file_operations import select_files, select_destination, move_files, category_analyzer
from gui_components import create_main_window, setup_ui, show_files_table

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

        # Sprawdź czy istnieją sugerowane lokalizacje
        suggested_destinations = {}
        for file_path in files:
            suggested = category_analyzer.get_suggested_destination(file_path)
            if suggested:
                if suggested not in suggested_destinations:
                    suggested_destinations[suggested] = []
                suggested_destinations[suggested].append(os.path.basename(file_path))

        # Jeśli mamy sugestie, zapytaj użytkownika
        destination = None
        if suggested_destinations and len(suggested_destinations) == 1:
            # Jeśli mamy tylko jedną sugestię dla wszystkich plików
            suggested = list(suggested_destinations.keys())[0]
            files_list = "\n".join(suggested_destinations[suggested][:5])
            if len(suggested_destinations[suggested]) > 5:
                files_list += f"\n... i {len(suggested_destinations[suggested]) - 5} więcej"

            response = messagebox.askyesno(
                "Sugerowana lokalizacja",
                f"Na podstawie historii przenoszenia, sugerowana lokalizacja to:\n{suggested}\n\n"
                f"Pliki do przeniesienia:\n{files_list}\n\n"
                f"Czy chcesz użyć tej lokalizacji?"
            )
            if response:
                destination = suggested

        # Jeśli nie wybrano sugerowanej lokalizacji, pozwól użytkownikowi wybrać folder
        if not destination:
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