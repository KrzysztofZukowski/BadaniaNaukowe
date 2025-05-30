import tkinter as tk
from tkinter import messagebox, ttk
import os
import sys
import traceback
import threading
import time

# Upewniamy się, że katalog z naszymi modułami jest w ścieżce Pythona
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

# Importujemy funkcje bezpośrednio
from file_operations import select_files, select_destination, move_files, category_analyzer
from gui_components import create_main_window, setup_ui, show_files_table

# Próbujemy zaimportować rozszerzony wizualizer, jeśli nie ma - używamy podstawowego
try:
    from enhanced_file_group_visualizer import EnhancedFileGroupVisualizer

    print("Używam rozszerzonego wizualizera grup z zaawansowanymi funkcjami")
    USE_ENHANCED_VISUALIZER = True
except ImportError:
    print("Nie mogę zaimportować rozszerzonego wizualizera, używam podstawowego")
    try:
        from file_group_visualizer import FileGroupVisualizer

        USE_ENHANCED_VISUALIZER = False
    except ImportError:
        print("Błąd: Nie można zaimportować żadnego wizualizera")
        USE_ENHANCED_VISUALIZER = False

# Sprawdź czy używamy rozszerzonego analizatora kategorii
try:
    from enhanced_category_analyzer import EnhancedCategoryAnalyzer

    print("Używam rozszerzonego analizatora kategorii z zaawansowanym grupowaniem")
    USE_ENHANCED_ANALYZER = True
except ImportError:
    print("Rozszerzony analizator niedostępny, używam podstawowego")
    USE_ENHANCED_ANALYZER = False


class ProgressDialog:
    """Klasa dla okna dialogowego postępu"""

    def __init__(self, parent, title="Analiza"):
        self.window = tk.Toplevel(parent)
        self.window.title(title)
        self.window.geometry("400x200")
        self.window.resizable(False, False)
        self.closed = False  # Dodaj flagę do śledzenia stanu

        # Wyśrodkuj okno
        self.window.transient(parent)
        self.window.grab_set()

        # Ramka główna
        main_frame = ttk.Frame(self.window, padding="20")
        main_frame.pack(fill="both", expand=True)

        # Etykieta tytułu
        title_label = ttk.Label(main_frame, text="Analiza w toku...",
                                font=("Arial", 12, "bold"))
        title_label.pack(pady=(0, 10))

        # Pasek postępu
        self.progress = ttk.Progressbar(main_frame, mode='indeterminate')
        self.progress.pack(fill="x", pady=(0, 10))
        self.progress.start()

        # Etykieta statusu
        self.status_label = ttk.Label(main_frame, text="Przygotowywanie analizy...",
                                      font=("Arial", 9))
        self.status_label.pack(pady=(0, 10))

        # Szczegóły analizy
        self.details_label = ttk.Label(main_frame, text="",
                                       font=("Arial", 8, "italic"),
                                       foreground="gray")
        self.details_label.pack()

    def update_status(self, status, details=""):
        """Aktualizuje status w oknie dialogowym"""
        if not self.closed:
            try:
                self.status_label.config(text=status)
                self.details_label.config(text=details)
                self.window.update()
            except tk.TclError:
                # Okno zostało już zamknięte
                self.closed = True

    def close(self):
        """Zamyka okno dialogowe"""
        if not self.closed:
            try:
                self.progress.stop()
                self.window.destroy()
                self.closed = True
            except tk.TclError:
                # Okno było już zamknięte
                self.closed = True


def main():
    """Główna funkcja programu z ulepszonymi funkcjami"""
    # Utworzenie głównego okna
    root = create_main_window()

    # Konfiguracja stylu dla ulepszonych funkcji
    style = ttk.Style()
    try:
        style.theme_use('clam')
    except:
        pass

    # Zmienna do przechowywania informacji o plikach
    files_info_list = []

    # Zmienna do przechowywania statystyk
    analysis_stats = {
        'last_analysis_time': 0,
        'total_groups_created': 0,
        'files_analyzed': 0,
        'similarity_calculations': 0
    }

    def show_capabilities():
        """Pokazuje możliwości systemu"""
        capabilities_window = tk.Toplevel(root)
        capabilities_window.title("Możliwości systemu")
        capabilities_window.geometry("600x500")

        # Tekst z możliwościami
        text_widget = tk.Text(capabilities_window, wrap=tk.WORD, padx=10, pady=10)
        text_widget.pack(fill="both", expand=True)

        capabilities_text = """"""

        text_widget.insert('1.0', capabilities_text)
        text_widget.config(state='disabled')

        # Przycisk zamknięcia
        close_btn = ttk.Button(capabilities_window, text="Zamknij",
                               command=capabilities_window.destroy)
        close_btn.pack(pady=10)

    # Funkcja do obsługi procesu przenoszenia
    def start_moving_process():
        nonlocal files_info_list, analysis_stats

        files = select_files()
        if not files:
            messagebox.showinfo("Informacja", "Nie wybrano żadnych plików.")
            return

        print(f"Wybrano {len(files)} plików do analizy:")
        for file in files:
            print(f"  {file}")

        # Pokazuj okno postępu dla dużych zbiorów
        progress_dialog = None
        if len(files) > 10:
            progress_dialog = ProgressDialog(root, "Analiza plików")
            progress_dialog.update_status("Analizuję nazwy plików...",
                                          f"Wykrywanie wzorców w {len(files)} plikach")

        try:
            # Sprawdź czy istnieją sugerowane lokalizacje
            suggested_destinations = {}
            suggestions_count = 0

            if progress_dialog:
                progress_dialog.update_status("Analizuję historię...",
                                              "Wykorzystuję dane historyczne")

            for file_path in files:
                suggested = category_analyzer.get_suggested_destination(file_path)
                if suggested:
                    suggestions_count += 1
                    if suggested not in suggested_destinations:
                        suggested_destinations[suggested] = []
                    suggested_destinations[suggested].append(os.path.basename(file_path))

            # Zamknij okno postępu
            if progress_dialog:
                progress_dialog.update_status("Analiza zakończona!",
                                              f"Znaleziono {suggestions_count} automatycznych sugestii")
                time.sleep(1)
                progress_dialog.close()

            # Pokaż statystyki
            if suggestions_count > 0:
                efficiency = (suggestions_count / len(files)) * 100
                message = (f"ANALIZA ZAKOŃCZONA!\n\n"
                           f"Efektywność: {efficiency:.1f}%\n"
                           f"Automatyczne sugestie: {suggestions_count}/{len(files)}\n"
                           f"Wykryte wzorce: {len(suggested_destinations)} lokalizacji\n\n"
                           f"System wykorzystał historię {len(category_analyzer.transfer_history.get('extensions', {}))} rozszerzeń "
                           f"i {len(category_analyzer.transfer_history.get('patterns', {}))} wzorców nazw.")

                messagebox.showinfo("Analiza", message)

            # Jeśli mamy sugestie, zapytaj użytkownika
            destination = None
            if suggested_destinations and len(suggested_destinations) == 1:
                # Jeśli system ma tylko jedną sugestię dla wszystkich plików
                suggested = list(suggested_destinations.keys())[0]
                files_list = "\n".join(suggested_destinations[suggested][:5])
                if len(suggested_destinations[suggested]) > 5:
                    files_list += f"\n... i {len(suggested_destinations[suggested]) - 5} więcej"

                response = messagebox.askyesno(
                    "Sugestia systemu",
                    f"REKOMENDACJA:\n\n"
                    f"Na podstawie analizy wzorców i historii, system sugeruje lokalizację:\n"
                    f"{suggested}\n\n"
                    f"Pliki do przeniesienia:\n{files_list}\n\n"
                    f"Pewność: {efficiency:.0f}%\n\n"
                    f"Czy chcesz użyć sugestii systemu?"
                )
                if response:
                    destination = suggested

            # Jeśli nie wybrano sugerowanej lokalizacji, pozwól użytkownikowi wybrać folder
            if not destination:
                destination = select_destination()
                if not destination:
                    messagebox.showinfo("Informacja", "Nie wybrano folderu docelowego.")
                    return

            print(f"Wybrano folder docelowy: {destination}")

            # Przenoszenie plików z monitorowaniem
            print(f"Rozpoczynam przenoszenie plików z analizą...")
            start_time = time.time()

            files_info_list = move_files(files, destination)

            # Aktualizuj statystyki - POPRAWIONE
            analysis_stats['last_analysis_time'] = time.time() - start_time
            analysis_stats['files_analyzed'] += len(files_info_list)

            # Bezpieczne pobieranie liczby podobieństw
            try:
                if USE_ENHANCED_ANALYZER and hasattr(category_analyzer, 'name_analyzer'):
                    similarity_cache_size = len(getattr(category_analyzer.name_analyzer, 'similarity_cache', {}))
                else:
                    similarity_cache_size = 0
                analysis_stats['similarity_calculations'] += similarity_cache_size
            except Exception as cache_error:
                print(f"Nie udało się pobrać statystyk cache: {cache_error}")
                analysis_stats['similarity_calculations'] = 0

            print(f"Zakończono przenoszenie plików. Otrzymano {len(files_info_list)} informacji o plikach.")

            # Liczenie statystyk
            success_count = len([f for f in files_info_list if f.status == "Przeniesiono"])
            failed_count = len(files_info_list) - success_count

            print(f"Sukces: {success_count}, Nieudane: {failed_count}")

            # Pokaż wyniki z statistykami
            if failed_count > 0:
                messagebox.showwarning(
                    "Ostrzeżenie",
                    f"WYNIKI TRANSFERU:\n\n"
                    f"Przeniesiono: {success_count}/{len(files_info_list)}\n"
                    f"Nieudane: {failed_count}\n\n"
                    f"Czas analizy: {analysis_stats['last_analysis_time']:.1f}s\n"
                    f"Cache Size: {analysis_stats['similarity_calculations']} calculations"
                )
            else:
                messagebox.showinfo(
                    "Sukces",
                    f"TRANSFER PLIKÓW ZAKOŃCZONY!\n\n"
                    f"Wszystkie pliki ({success_count}) zostały pomyślnie przeniesione\n"
                    f"Lokalizacja: {destination}\n\n"
                    f"Statystyki:\n"
                    f"Czas analizy: {analysis_stats['last_analysis_time']:.1f}s\n"
                    f"Cache podobieństw: {analysis_stats['similarity_calculations']}\n"
                    f"Łącznie przeanalizowano: {analysis_stats['files_analyzed']} plików"
                )

            # Wyświetlenie tabeli z informacjami o plikach
            show_files_table(files_info_list, category_analyzer)

            # Pytanie o wizualizację grup z informacjami
            if len(files_info_list) > 1:
                if USE_ENHANCED_VISUALIZER:
                    # Oblicz potencjalne grupy dla lepszej informacji - POPRAWIONE
                    potential_groups = 0
                    try:
                        if hasattr(category_analyzer, 'smart_group_files_by_name'):
                            temp_groups = category_analyzer.smart_group_files_by_name(files_info_list)
                            potential_groups = len(temp_groups)
                        else:
                            potential_groups = "kilka"
                    except Exception as group_error:
                        print(f"Nie udało się obliczyć grup: {group_error}")
                        potential_groups = "kilka"

                    message = (
                        "ZAAWANSOWANA WIZUALIZACJA",
                        f"GOTOWE DO ANALIZY!\n\n"
                        f"Wykryto potencjalnie {potential_groups} zaawansowanych grup\n"
                        f"Czy chcesz uruchomić zaawansowaną wizualizację?"
                    )
                else:
                    message = (
                        "Podstawowa wizualizacja grup",
                        "Czy chcesz wyświetlić podstawową wizualizację grup plików?"
                    )

                response = messagebox.askyesno(message[0], message[1])
                if response:
                    show_group_visualizer()

        except Exception as e:
            # Zamknij okno postępu w przypadku błędu
            if progress_dialog:
                progress_dialog.close()

            print(f"KRYTYCZNY BŁĄD w procesie przenoszenia: {e}")
            traceback.print_exc()
            messagebox.showerror(
                "Błąd",
                f"Wystąpił błąd podczas przenoszenia plików:\n{str(e)}\n\n"
                f"Statystyki przed błędem:\n"
                f"Czas analizy: {analysis_stats.get('last_analysis_time', 0):.1f}s\n"
                f"Plików przeanalizowano: {analysis_stats.get('files_analyzed', 0)}"
            )

    # Funkcja do wyświetlania wizualizacji grup
    def show_group_visualizer():
        if not files_info_list:
            messagebox.showinfo("Informacja", "Brak plików do grupowania.")
            return

        try:
            # Pokazuj okno postępu dla zaawansowanej analizy
            progress_dialog = None
            if USE_ENHANCED_VISUALIZER and len(files_info_list) > 5:
                progress_dialog = ProgressDialog(root, "Zaawansowana Analiza")
                progress_dialog.update_status("Uruchamianie systemu...",
                                              "Inicjalizacja algorytmów grupowania")

            print("Tworzenie zaawansowanego wizualizera grup...")

            if USE_ENHANCED_VISUALIZER:
                if progress_dialog:
                    progress_dialog.update_status("Tworzenie wizualizera...",
                                                  "Ładowanie zaawansowanych funkcji")
                    time.sleep(0.5)

                visualizer = EnhancedFileGroupVisualizer(root, files_info_list, category_analyzer)
                print("Rozszerzony wizualizer grup utworzony pomyślnie")

                if progress_dialog:
                    progress_dialog.update_status("System gotowy!", "Wizualizer załadowany")
                    time.sleep(0.5)
                    progress_dialog.close()

            else:
                if progress_dialog:
                    progress_dialog.close()

                visualizer = FileGroupVisualizer(root, files_info_list, category_analyzer)
                print("Podstawowy wizualizer grup utworzony pomyślnie")

        except Exception as e:
            if progress_dialog:
                progress_dialog.close()

            print(f"BŁĄD podczas tworzenia wizualizera grup: {e}")
            traceback.print_exc()
            messagebox.showerror(
                "Błąd Wizualizera",
                f"Wystąpił błąd podczas tworzenia wizualizera grup:\n{str(e)}\n\n"
                f"Spróbuj ponownie lub skontaktuj się z pomocą techniczną."
            )

    def show_statistics():
        """Pokazuje statystyki systemu"""
        stats_window = tk.Toplevel(root)
        stats_window.title("Statystyki systemu")
        stats_window.geometry("500x400")

        # Ramka główna
        main_frame = ttk.Frame(stats_window, padding="10")
        main_frame.pack(fill="both", expand=True)

        # Tytuł
        title_label = ttk.Label(main_frame, text="STATYSTYKI SYSTEMU",
                                font=("Arial", 14, "bold"))
        title_label.pack(pady=(0, 20))

        # Notebook dla różnych kategorii statystyk
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill="both", expand=True)

        # Zakładka 1: Statystyki sesji
        session_frame = ttk.Frame(notebook)
        notebook.add(session_frame, text="Sesja")

        session_text = tk.Text(session_frame, wrap=tk.WORD, padx=10, pady=10)
        session_text.pack(fill="both", expand=True)

        session_stats = f"""STATYSTYKI BIEŻĄCEJ SESJI:

Ostatni czas analizy: {analysis_stats['last_analysis_time']:.2f} sekund
Plików przeanalizowanych: {analysis_stats['files_analyzed']}
Obliczenia podobieństwa: {analysis_stats['similarity_calculations']}
Grupy utworzone: {analysis_stats['total_groups_created']}

EFEKTYWNOŚĆ:
{'Wysoka' if analysis_stats['files_analyzed'] > 10 else 'Średnia' if analysis_stats['files_analyzed'] > 0 else 'Brak danych'}

ROZMIAR CACHE:
Cache podobieństw: {analysis_stats['similarity_calculations']} wpisów

KONFIGURACJA ALGORYTMÓW:
• Próg podobieństwa: 55%
• Próg fuzzy matching: 80%  
• Próg semantyczny: 70%
• Multi-algorytmiczne ważenie: {'AKTYWNE' if USE_ENHANCED_ANALYZER else 'NIEAKTYWNE'}
"""

        session_text.insert('1.0', session_stats)
        session_text.config(state='disabled')

        # Zakładka 2: Historia
        history_frame = ttk.Frame(notebook)
        notebook.add(history_frame, text="Historia")

        history_text = tk.Text(history_frame, wrap=tk.WORD, padx=10, pady=10)
        history_text.pack(fill="both", expand=True)

        # Statystyki z historii
        ext_count = len(category_analyzer.transfer_history.get('extensions', {}))
        pattern_count = len(category_analyzer.transfer_history.get('patterns', {}))
        dest_count = len(category_analyzer.transfer_history.get('destinations', {}))

        history_stats_text = f"""HISTORIA DANYCH:

Rozszerzenia w bazie: {ext_count}
Wzorce nazw: {pattern_count}  
Lokalizacje docelowe: {dest_count}

SKUTECZNOŚĆ PREDYKCJI:
System może przewidzieć lokalizację dla:
• {ext_count} typów rozszerzeń
• {pattern_count} wzorców nazw plików

REKOMENDACJE:
{'System ma wystarczająco danych do dokładnych predykcji' if ext_count > 5 else 'System potrzebuje więcej danych do nauki'}

OSTATNIA AKTUALIZACJA:
Historia została zaktualizowana podczas ostatniego przenoszenia plików.
"""

        history_text.insert('1.0', history_stats_text)
        history_text.config(state='disabled')

        # Przycisk zamknięcia
        close_btn = ttk.Button(main_frame, text="Zamknij", command=stats_window.destroy)
        close_btn.pack(pady=10)

    # Funkcja konfiguracji UI z dodatkowymi funkcjami
    def setup_enhanced_ui(root):
        # Konfiguracja okna głównego
        root.configure(bg='#f5f5f5')

        # Ramka główna
        main_frame = ttk.Frame(root)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Banner tytułowy
        if USE_ENHANCED_ANALYZER and USE_ENHANCED_VISUALIZER:
            title = "SYSTEM ORGANIZACJI PLIKÓW"
            title_color = "darkblue"
            subtitle_color = "darkgreen"
        else:
            title = "Program do przenoszenia i organizacji plików"
            title_color = "black"
            subtitle_color = "gray"

        title_label = ttk.Label(main_frame, text=title,
                                foreground=title_color, font=("Arial", 16, "bold"))
        title_label.pack(pady=(0, 10))

        # Ramka dla głównych przycisków
        buttons_frame = ttk.LabelFrame(main_frame, text="Główne funkcje", padding="15")
        buttons_frame.pack(fill="x", pady=(0, 20))

        # Przycisk do wyboru plików - GŁÓWNY
        main_button_text = "Rozpocznij Analizę" if USE_ENHANCED_ANALYZER else "Wybierz pliki do przeniesienia"
        select_files_button = ttk.Button(
            buttons_frame,
            text=main_button_text,
            command=start_moving_process,
            style='Accent.TButton'
        )
        select_files_button.pack(fill="x", pady=(0, 10))

        # Dodatkowe przyciski
        buttons_row1 = ttk.Frame(buttons_frame)
        buttons_row1.pack(fill="x", pady=(0, 10))

        # Przycisk do wizualizacji grup
        visualize_text = ("Zaawansowana Wizualizacja" if USE_ENHANCED_VISUALIZER
                          else "Wyświetl grupowanie")
        visualize_button = ttk.Button(
            buttons_row1,
            text=visualize_text,
            command=show_group_visualizer
        )
        visualize_button.pack(side="left", fill="x", expand=True, padx=(0, 5))

        # Przycisk statystyk
        if USE_ENHANCED_ANALYZER:
            stats_button = ttk.Button(
                buttons_row1,
                text="Statystyki",
                command=show_statistics
            )
            stats_button.pack(side="right", fill="x", expand=True, padx=(5, 0))

        # Informacje o aplikacji
        info_frame = ttk.LabelFrame(main_frame, text="Informacje", padding="15")
        info_frame.pack(fill="both", expand=True)

        info_text = """"""

        if USE_ENHANCED_ANALYZER:
            info_text += """✅ SYSTEM ZAAWANSOWANY AKTYWNY
• Inteligentne grupowanie plików
• Automatyczne wykrywanie podobieństw
• Predykcja lokalizacji na podstawie historii"""

        info_text += "\n\nProgram zapamiętuje historię i proponuje najlepsze lokalizacje."

        info_label = ttk.Label(info_frame, text=info_text, justify=tk.LEFT,
                               font=("Arial", 9), wraplength=500)
        info_label.pack(pady=(0, 15))

        # Ramka dolna z przyciskiem zamknięcia
        bottom_frame = ttk.Frame(main_frame)
        bottom_frame.pack(fill="x", pady=(10, 0))

        close_button = ttk.Button(bottom_frame, text="Zamknij", command=root.destroy)
        close_button.pack()

        # Konfiguracja stylów
        try:
            style = ttk.Style()
            style.configure('Accent.TButton', font=('Arial', 11, 'bold'))
        except:
            pass

    # Konfiguracja interfejsu użytkownika z rozszerzoną wersją funkcji
    setup_enhanced_ui(root)

    # Uruchomienie głównej pętli aplikacji
    root.mainloop()


if __name__ == "__main__":
    try:
        if USE_ENHANCED_ANALYZER and USE_ENHANCED_VISUALIZER:
            print("Uruchamianie programu z pełnym systemem zaawansowanym...")
            print("Aktywne funkcje: Multi-algorytmiczne grupowanie + Zaawansowana wizualizacja")
        elif USE_ENHANCED_ANALYZER:
            print("Uruchamianie programu z zaawansowanym analizatorem...")
            print("Aktywne funkcje: Multi-algorytmiczne grupowanie")
        elif USE_ENHANCED_VISUALIZER:
            print("Uruchamianie programu z zaawansowaną wizualizacją...")
            print("Aktywne funkcje: Ulepszona wizualizacja grup")
        else:
            print("Uruchamianie programu w trybie podstawowym...")

        main()
    except Exception as e:
        print(f"Wystąpił krytyczny błąd: {e}")
        traceback.print_exc()

        # Próba wyświetlenia okna dialogowego z błędem
        try:
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror(
                "Krytyczny błąd systemu",
                f"Wystąpił krytyczny błąd podczas uruchamiania programu:\n\n{str(e)}\n\n"
                f"System może być nieosiągalny.\n"
                f"Spróbuj ponownie lub skontaktuj się z pomocą techniczną."
            )
        except:
            print("Nie można wyświetlić okna dialogowego błędu")
            pass