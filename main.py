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
from file_group_visualizer import FileGroupVisualizer


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

        # Wyświetlenie tabeli z informacjami o plikach - przekazujemy category_analyzer
        show_files_table(files_info_list, category_analyzer)

        # Pytanie o wyświetlenie wizualizacji grup
        if len(files_info_list) > 1:  # Nie ma sensu grupować pojedynczego pliku
            response = messagebox.askyesno(
                "Grupowanie plików",
                "Czy chcesz wyświetlić zaawansowaną wizualizację grup plików?"
            )
            if response:
                show_group_visualizer()

    # Funkcja do wyświetlania wizualizacji grup
    def show_group_visualizer():
        if not files_info_list:
            messagebox.showinfo("Informacja", "Brak plików do grupowania.")
            return

        # Utworzenie wizualizera grup
        visualizer = FileGroupVisualizer(root, files_info_list, category_analyzer)

    # Zmodyfikowana funkcja konfiguracji UI z dodatkowym przyciskiem
    def setup_enhanced_ui(root):
        # Etykieta informacyjna
        label = tk.Label(root, text="Program do przenoszenia plików", font=("Arial", 14))
        label.pack(pady=10)

        # Przycisk do wyboru plików
        select_files_button = tk.Button(
            root,
            text="Wybierz pliki do przeniesienia",
            command=start_moving_process,
            width=30
        )
        select_files_button.pack(pady=10)

        # Przycisk do wizualizacji grup (aktywny tylko gdy są dane)
        visualize_button = tk.Button(
            root,
            text="Wyświetl wizualizację grup",
            command=show_group_visualizer,
            width=30
        )
        visualize_button.pack(pady=10)

        # Dodatkowe informacje o aplikacji
        info_text = """
Program pomaga przenosić pliki i kategoryzuje je na podstawie:
- Rozszerzenia pliku
- Nazwy pliku
- Rozmiaru pliku
- Daty utworzenia/modyfikacji
- Wzorców w nazwie
- I wielu innych czynników...

Program zapamiętuje historię przenoszenia i proponuje najlepsze lokalizacje.
        """
        info_label = tk.Label(root, text=info_text, justify=tk.LEFT, padx=20)
        info_label.pack(pady=10)

        # Przycisk zamknięcia
        close_button = tk.Button(
            root,
            text="Zamknij",
            command=root.destroy,
            width=20
        )
        close_button.pack(pady=10)

    # Konfiguracja interfejsu użytkownika z rozszerzoną wersją funkcji
    setup_enhanced_ui(root)

    # Uruchomienie głównej pętli aplikacji
    root.mainloop()


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Wystąpił błąd: {e}")
        import traceback

        traceback.print_exc()