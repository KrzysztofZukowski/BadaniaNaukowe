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
from auto_folder_organizer import AutoFolderOrganizer

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
        self.closed = False

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
                self.closed = True

    def close(self):
        """Zamyka okno dialogowe"""
        if not self.closed:
            try:
                self.progress.stop()
                self.window.destroy()
                self.closed = True
            except tk.TclError:
                self.closed = True


class AutoOrganizeDialog:
    """Okno dialogowe do konfiguracji automatycznego organizowania"""

    def __init__(self, parent, files_info, auto_organizer):
        self.parent = parent
        self.files_info = files_info
        self.auto_organizer = auto_organizer
        self.result = None

        # Utworzenie okna
        self.window = tk.Toplevel(parent)
        self.window.title("Automatyczne organizowanie plików")
        self.window.geometry("800x700")
        self.window.resizable(True, True)

        # Wyśrodkuj okno
        self.window.transient(parent)
        self.window.grab_set()

        self.setup_ui()
        self.preview_structure()

    def setup_ui(self):
        """Konfiguruje interfejs użytkownika"""

        # Ramka główna
        main_frame = ttk.Frame(self.window, padding="10")
        main_frame.pack(fill="both", expand=True)

        # Tytuł
        title_label = ttk.Label(main_frame,
                                text="🗂️ AUTOMATYCZNE ORGANIZOWANIE PLIKÓW",
                                font=("Arial", 14, "bold"),
                                foreground="darkblue")
        title_label.pack(pady=(0, 20))

        # Opis
        desc_label = ttk.Label(main_frame,
                               text="Wybierz sposób organizacji plików w foldery:",
                               font=("Arial", 10))
        desc_label.pack(pady=(0, 15))

        # Ramka z opcjami organizacji
        options_frame = ttk.LabelFrame(main_frame, text="Tryby organizacji", padding="10")
        options_frame.pack(fill="x", pady=(0, 15))

        # Zmienna do przechowywania wybranego trybu
        self.organization_mode = tk.StringVar(value="full")

        # Pobierz dostępne tryby
        modes = self.auto_organizer.get_organization_modes()

        for mode_key, mode_info in modes.items():
            # Ramka dla każdej opcji
            mode_frame = ttk.Frame(options_frame)
            mode_frame.pack(fill="x", pady=5)

            # Radiobutton
            rb = ttk.Radiobutton(mode_frame,
                                 text=mode_info["name"],
                                 value=mode_key,
                                 variable=self.organization_mode,
                                 command=self.preview_structure)
            rb.pack(side="left")

            # Opis
            desc = ttk.Label(mode_frame,
                             text=mode_info["description"],
                             font=("Arial", 9),
                             foreground="gray")
            desc.pack(side="left", padx=(10, 0))

            # Przykład
            example = ttk.Label(mode_frame,
                                text=f"Przykład: {mode_info['example']}",
                                font=("Arial", 8, "italic"),
                                foreground="blue")
            example.pack(side="left", padx=(20, 0))

        # Ramka z podglądem
        preview_frame = ttk.LabelFrame(main_frame, text="Podgląd struktury folderów", padding="10")
        preview_frame.pack(fill="both", expand=True, pady=(0, 15))

        # Tekst z podglądem
        self.preview_text = tk.Text(preview_frame,
                                    wrap=tk.WORD,
                                    font=("Courier", 9),
                                    height=15)

        # Pasek przewijania
        preview_scrollbar = ttk.Scrollbar(preview_frame, orient="vertical", command=self.preview_text.yview)
        self.preview_text.configure(yscrollcommand=preview_scrollbar.set)

        preview_scrollbar.pack(side="right", fill="y")
        self.preview_text.pack(fill="both", expand=True)

        # Ramka z przyciskami
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.pack(fill="x", pady=(10, 0))

        # Checkbox dla trybu symulacji
        self.dry_run_var = tk.BooleanVar(value=True)
        dry_run_cb = ttk.Checkbutton(buttons_frame,
                                     text="Tryb symulacji (bez rzeczywistego przenoszenia)",
                                     variable=self.dry_run_var)
        dry_run_cb.pack(anchor="w")

        # Checkbox dla używania istniejącej struktury
        self.use_existing_var = tk.BooleanVar(value=True)
        existing_cb = ttk.Checkbutton(buttons_frame,
                                      text="🔄 Używaj istniejących folderów (dodawaj do istniejącej struktury)",
                                      variable=self.use_existing_var)
        existing_cb.pack(anchor="w")

        # Opis opcji
        desc_existing = ttk.Label(buttons_frame,
                                  text="   ↳ Jeśli foldery już istnieją, pliki zostaną dodane do nich. Nowe foldery będą utworzone tylko gdy potrzeba.",
                                  font=("Arial", 8, "italic"),
                                  foreground="gray")
        desc_existing.pack(anchor="w", padx=(20, 0))

        # Przyciski akcji
        action_buttons = ttk.Frame(buttons_frame)
        action_buttons.pack(fill="x", pady=(10, 0))

        ttk.Button(action_buttons, text="Anuluj", command=self.cancel).pack(side="right", padx=(5, 0))
        ttk.Button(action_buttons, text="Wykonaj", command=self.execute).pack(side="right")

    def preview_structure(self):
        """Generuje podgląd struktury folderów"""
        try:
            mode = self.organization_mode.get()
            structure = self.auto_organizer.analyze_folder_structure(self.files_info, mode)

            # Wyczyść poprzedni podgląd
            self.preview_text.delete('1.0', tk.END)

            # Generuj tekst podglądu
            preview_text = f"Podgląd struktury dla trybu: {mode}\n"
            preview_text += "=" * 50 + "\n\n"

            # Sortuj foldery alfabetycznie
            sorted_folders = sorted(structure.items())

            for folder_path, files in sorted_folders:
                # Nazwa folderu
                preview_text += f"📁 {folder_path}/\n"

                # Lista plików (maksymalnie 5)
                for i, filename in enumerate(files[:5]):
                    preview_text += f"   📄 {filename}\n"

                # Jeśli więcej plików
                if len(files) > 5:
                    preview_text += f"   ... i {len(files) - 5} więcej plików\n"

                preview_text += "\n"

            # Statystyki
            total_folders = len(structure)
            total_files = sum(len(files) for files in structure.values())

            preview_text += f"\n📊 STATYSTYKI:\n"
            preview_text += f"Liczba folderów: {total_folders}\n"
            preview_text += f"Liczba plików: {total_files}\n"

            # Wyświetl podgląd
            self.preview_text.insert('1.0', preview_text)

        except Exception as e:
            error_text = f"Błąd generowania podglądu: {e}\n\n{traceback.format_exc()}"
            self.preview_text.delete('1.0', tk.END)
            self.preview_text.insert('1.0', error_text)

    def execute(self):
        """Wykonuje automatyczne organizowanie"""
        self.result = {
            'mode': self.organization_mode.get(),
            'dry_run': self.dry_run_var.get(),
            'use_existing': self.use_existing_var.get(),
            'execute': True
        }
        self.window.destroy()

    def cancel(self):
        """Anuluje operację"""
        self.result = {'execute': False}
        self.window.destroy()


def main():
    """Główna funkcja programu z automatycznym organizowaniem"""
    # Utworzenie głównego okna
    root = create_main_window()

    # Konfiguracja stylu
    style = ttk.Style()
    try:
        style.theme_use('clam')
    except:
        pass

    # Zmienne globalne
    files_info_list = []
    analysis_stats = {
        'last_analysis_time': 0,
        'total_groups_created': 0,
        'files_analyzed': 0,
        'similarity_calculations': 0
    }

    # Inicjalizacja organizatora folderów
    auto_organizer = AutoFolderOrganizer(category_analyzer)

    def start_moving_process():
        """Standardowy proces przenoszenia (bez automatycznego organizowania)"""
        nonlocal files_info_list, analysis_stats

        files = select_files()
        if not files:
            messagebox.showinfo("Informacja", "Nie wybrano żadnych plików.")
            return

        print(f"Wybrano {len(files)} plików do analizy:")

        progress_dialog = None
        if len(files) > 10:
            progress_dialog = ProgressDialog(root, "Analiza plików")
            progress_dialog.update_status("Analizuję nazwy plików...",
                                          f"Wykrywanie wzorców w {len(files)} plikach")

        try:
            if progress_dialog:
                progress_dialog.update_status("Analiza zakończona!")
                time.sleep(1)
                progress_dialog.close()

            destination = select_destination()
            if not destination:
                messagebox.showinfo("Informacja", "Nie wybrano folderu docelowego.")
                return

            print(f"Rozpoczynam przenoszenie plików z analizą...")
            start_time = time.time()

            files_info_list = move_files(files, destination)

            # Aktualizuj statystyki
            analysis_stats['last_analysis_time'] = time.time() - start_time
            analysis_stats['files_analyzed'] += len(files_info_list)

            print(f"Zakończono przenoszenie plików. Otrzymano {len(files_info_list)} informacji o plikach.")

            # Wyświetlenie tabeli z informacjami o plikach
            show_files_table(files_info_list, category_analyzer)

            # Pytanie o wizualizację grup
            if len(files_info_list) > 1:
                show_group_visualizer()

        except Exception as e:
            if progress_dialog:
                progress_dialog.close()
            print(f"KRYTYCZNY BŁĄD w procesie przenoszenia: {e}")
            traceback.print_exc()
            messagebox.showerror("Błąd", f"Wystąpił błąd podczas przenoszenia plików:\n{str(e)}")

    def start_auto_organize_process():
        """Nowy proces z automatycznym organizowaniem folderów - NAPRAWIONA WERSJA"""
        nonlocal files_info_list, analysis_stats

        files = select_files()
        if not files:
            messagebox.showinfo("Informacja", "Nie wybrano żadnych plików.")
            return

        print(f"Wybrano {len(files)} plików do automatycznego organizowania:")

        # Analizuj pliki bez przenoszenia
        progress_dialog = ProgressDialog(root, "Analiza plików")
        progress_dialog.update_status("Analizuję pliki...", "Przygotowywanie do organizowania")

        try:
            # WSZYSTKIE IMPORTY NA POCZĄTKU
            from models import FileInfo
            from datetime import datetime
            from file_size_reader import FileSizeReader
            from file_analyzer import get_mime_type, get_file_signature, extract_keywords, analyze_headers

            # Pomocnicza funkcja formatowania daty
            def safe_format_datetime(timestamp):
                try:
                    return datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
                except:
                    return "Data nieznana"

            # Stwórz tymczasowe obiekty FileInfo dla analizy
            temp_files_info = []

            for i, file_path in enumerate(files):
                try:
                    # Aktualizuj progress dialog
                    file_name = os.path.basename(file_path)
                    progress_dialog.update_status(
                        f"Analizuję: {file_name}",
                        f"Plik {i + 1} z {len(files)}"
                    )

                    # Sprawdź czy plik istnieje
                    if not os.path.exists(file_path):
                        print(f"Plik nie istnieje: {file_path}")
                        continue

                    # Podstawowe informacje o pliku
                    name, extension = os.path.splitext(file_name)

                    # Pobierz statystyki pliku
                    try:
                        file_stats = os.stat(file_path)
                        file_size = FileSizeReader.get_file_size(file_path)
                        creation_date = safe_format_datetime(file_stats.st_ctime)
                        modification_date = safe_format_datetime(file_stats.st_mtime)
                    except Exception as stat_error:
                        print(f"Błąd statystyk dla {file_name}: {stat_error}")
                        file_size = 0
                        creation_date = "Data nieznana"
                        modification_date = "Data nieznana"

                    # Analiza zaawansowana - z obsługą błędów
                    try:
                        mime_type = get_mime_type(file_path)
                    except Exception:
                        mime_type = "nieznany"

                    try:
                        file_signature = get_file_signature(file_path)
                    except Exception:
                        file_signature = "nieznana"

                    try:
                        keywords = extract_keywords(file_path)
                    except Exception:
                        keywords = "brak"

                    try:
                        headers_info = analyze_headers(file_path)
                    except Exception:
                        headers_info = "brak"

                    # Kategoryzacja
                    try:
                        categorization = category_analyzer.categorize_file(file_path)
                    except Exception as cat_error:
                        print(f"Błąd kategoryzacji dla {file_name}: {cat_error}")
                        # Domyślna kategoryzacja
                        categorization = {
                            'kategoria_rozszerzenia': 'nieznana',
                            'kategoria_nazwy': [],
                            'sugerowane_lokalizacje': [],
                            'kategoria_wielkości': 'nieznana',
                            'kategoria_daty': 'nieznana',
                            'kategoria_przedmiotu': [],
                            'kategoria_czasowa': [],
                            'wszystkie_kategorie': []
                        }

                    # Utwórz obiekt FileInfo
                    file_info = FileInfo(
                        name, extension, file_path, "", "Do organizacji",
                        file_size, creation_date, modification_date, "",
                        mime_type, file_signature, keywords, headers_info,
                        categorization.get('kategoria_rozszerzenia', 'nieznana'),
                        categorization.get('kategoria_nazwy', []),
                        categorization.get('sugerowane_lokalizacje', []),
                        categorization.get('kategoria_wielkości', 'nieznana'),
                        categorization.get('kategoria_daty', 'nieznana'),
                        categorization.get('kategoria_przedmiotu', []),
                        categorization.get('kategoria_czasowa', []),
                        categorization.get('wszystkie_kategorie', [])
                    )

                    temp_files_info.append(file_info)
                    print(f"✅ Przeanalizowano: {file_name}")

                except Exception as e:
                    print(f"❌ Błąd analizy pliku {file_path}: {e}")
                    traceback.print_exc()
                    continue

            progress_dialog.close()

            if not temp_files_info:
                messagebox.showerror("Błąd", "Nie udało się przeanalizować żadnego pliku.")
                return

            print(f"✅ Pomyślnie przeanalizowano {len(temp_files_info)} z {len(files)} plików")

            # Pokaż okno konfiguracji automatycznego organizowania
            dialog = AutoOrganizeDialog(root, temp_files_info, auto_organizer)
            root.wait_window(dialog.window)

            if not dialog.result or not dialog.result['execute']:
                print("Anulowano automatyczne organizowanie")
                return

            # Wybierz folder docelowy
            destination = select_destination()
            if not destination:
                messagebox.showinfo("Informacja", "Nie wybrano folderu docelowego.")
                return

            # Generuj mapowanie plików
            organization_mode = dialog.result['mode']
            dry_run = dialog.result['dry_run']
            use_existing = dialog.result['use_existing']

            print(f"Generowanie struktury folderów...")
            file_mapping = auto_organizer.generate_folder_structure(
                destination, temp_files_info, organization_mode
            )

            # Wykonaj przenoszenie z opcją używania istniejącej struktury
            print(f"Wykonywanie {'symulacji' if dry_run else 'przenoszenia'}...")
            results = auto_organizer.create_folders_and_move_files(
                file_mapping, dry_run, use_existing
            )

            # Aktualizuj statystyki
            files_info_list = temp_files_info
            analysis_stats['files_analyzed'] += len(files_info_list)

            # Pokaż wyniki
            show_organize_results(results, dry_run)

            # Wyświetl tabelę z informacjami
            show_files_table(files_info_list, category_analyzer)

        except Exception as e:
            if 'progress_dialog' in locals():
                progress_dialog.close()
            print(f"BŁĄD w procesie automatycznego organizowania: {e}")
            traceback.print_exc()
            messagebox.showerror("Błąd", f"Wystąpił błąd podczas automatycznego organizowania:\n{str(e)}")

    def show_organize_results(results, dry_run):
        """Wyświetla wyniki automatycznego organizowania"""
        # Okno wyników
        results_window = tk.Toplevel(root)
        results_window.title("Wyniki automatycznego organizowania")
        results_window.geometry("600x500")

        # Ramka główna
        main_frame = ttk.Frame(results_window, padding="10")
        main_frame.pack(fill="both", expand=True)

        # Tytuł
        title = "🎯 WYNIKI SYMULACJI" if dry_run else "✅ WYNIKI ORGANIZOWANIA"
        title_label = ttk.Label(main_frame, text=title, font=("Arial", 14, "bold"))
        title_label.pack(pady=(0, 15))

        # Statystyki
        stats_frame = ttk.LabelFrame(main_frame, text="Statystyki", padding="10")
        stats_frame.pack(fill="x", pady=(0, 15))

        ttk.Label(stats_frame, text=f"Pomyślnie przeniesione: {len(results['success'])}",
                  font=("Arial", 10)).pack(anchor="w")
        ttk.Label(stats_frame, text=f"Błędy: {len(results['failed'])}",
                  font=("Arial", 10)).pack(anchor="w")
        ttk.Label(stats_frame, text=f"Nowe foldery: {len(results['folders_created'])}",
                  font=("Arial", 10)).pack(anchor="w")
        ttk.Label(stats_frame, text=f"Ponownie użyte foldery: {len(results.get('folders_reused', set()))}",
                  font=("Arial", 10)).pack(anchor="w")

        # Lista wyników
        results_frame = ttk.LabelFrame(main_frame, text="Szczegóły", padding="10")
        results_frame.pack(fill="both", expand=True, pady=(0, 15))

        # Tekst z wynikami
        results_text = tk.Text(results_frame, wrap=tk.WORD, font=("Courier", 9))
        results_scrollbar = ttk.Scrollbar(results_frame, orient="vertical", command=results_text.yview)
        results_text.configure(yscrollcommand=results_scrollbar.set)

        results_scrollbar.pack(side="right", fill="y")
        results_text.pack(fill="both", expand=True)

        # Generuj tekst wyników
        text_content = ""

        if results['success']:
            text_content += "✅ POMYŚLNIE PRZENIESIONE:\n"
            for item in results['success'][:20]:  # Pokaż maksymalnie 20
                text_content += f"  📄 {item['file_name']}\n"
            if len(results['success']) > 20:
                text_content += f"  ... i {len(results['success']) - 20} więcej\n"
            text_content += "\n"

        if results['failed']:
            text_content += "❌ BŁĘDY:\n"
            for item in results['failed']:
                text_content += f"  ❌ {os.path.basename(item['source'])}: {item['error']}\n"
            text_content += "\n"

        if results.get('folders_reused'):
            text_content += "♻️  PONOWNIE UŻYTE FOLDERY:\n"
            for folder in sorted(results['folders_reused'])[:10]:  # Pokaż maksymalnie 10
                text_content += f"  ♻️  {os.path.relpath(folder) if os.path.exists(folder) else folder}\n"
            if len(results['folders_reused']) > 10:
                text_content += f"  ... i {len(results['folders_reused']) - 10} więcej\n"
            text_content += "\n"

        if results['folders_created']:
            text_content += "📁 NOWO UTWORZONE FOLDERY:\n"
            for folder in sorted(results['folders_created'])[:15]:  # Pokaż maksymalnie 15
                text_content += f"  📁 {os.path.relpath(folder) if os.path.exists(folder) else folder}\n"
            if len(results['folders_created']) > 15:
                text_content += f"  ... i {len(results['folders_created']) - 15} więcej\n"

        results_text.insert('1.0', text_content)

        # Przycisk zamknięcia
        ttk.Button(main_frame, text="Zamknij", command=results_window.destroy).pack()

    def show_group_visualizer():
        """Wyświetla wizualizację grup"""
        if not files_info_list:
            messagebox.showinfo("Informacja", "Brak plików do grupowania.")
            return

        try:
            if USE_ENHANCED_VISUALIZER:
                visualizer = EnhancedFileGroupVisualizer(root, files_info_list, category_analyzer)
            else:
                visualizer = FileGroupVisualizer(root, files_info_list, category_analyzer)
        except Exception as e:
            print(f"BŁĄD podczas tworzenia wizualizera grup: {e}")
            messagebox.showerror("Błąd Wizualizera", f"Wystąpił błąd podczas tworzenia wizualizera grup:\n{str(e)}")

    def setup_enhanced_ui_with_auto_organize(root):
        """Konfiguruje rozszerzony interfejs z automatycznym organizowaniem"""
        root.configure(bg='#f5f5f5')

        # Ramka główna
        main_frame = ttk.Frame(root)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Banner tytułowy
        title = "🗂️ SYSTEM ORGANIZACJI PLIKÓW Z AUTO-FOLDERAMI"
        title_label = ttk.Label(main_frame, text=title,
                                foreground="darkblue", font=("Arial", 16, "bold"))
        title_label.pack(pady=(0, 10))

        # Ramka dla głównych przycisków
        buttons_frame = ttk.LabelFrame(main_frame, text="Główne funkcje", padding="15")
        buttons_frame.pack(fill="x", pady=(0, 20))

        # Przycisk automatycznego organizowania - GŁÓWNY
        auto_organize_button = ttk.Button(
            buttons_frame,
            text="🎯 Automatyczne Organizowanie",
            command=start_auto_organize_process,
            style='Accent.TButton'
        )
        auto_organize_button.pack(fill="x", pady=(0, 10))

        # Przycisk standardowego przenoszenia
        standard_button = ttk.Button(
            buttons_frame,
            text="📁 Standardowe Przenoszenie",
            command=start_moving_process
        )
        standard_button.pack(fill="x", pady=(0, 10))

        # Dodatkowe przyciski w rzędzie
        buttons_row = ttk.Frame(buttons_frame)
        buttons_row.pack(fill="x", pady=(0, 10))

        # Przycisk wizualizacji
        visualize_button = ttk.Button(
            buttons_row,
            text="📊 Wizualizacja Grup",
            command=show_group_visualizer
        )
        visualize_button.pack(side="left", fill="x", expand=True, padx=(0, 5))

        # Informacje o aplikacji
        info_frame = ttk.LabelFrame(main_frame, text="Informacje", padding="15")
        info_frame.pack(fill="both", expand=True)

        info_text = """🎯 AUTOMATYCZNE ORGANIZOWANIE:
• Inteligentna hierarchia folderów: Typ → Data → Tematyka
• 4 tryby organizacji do wyboru
• Podgląd struktury przed wykonaniem
• Tryb symulacji bezpiecznego testowania

📁 STANDARDOWE PRZENOSZENIE:
• Klasyczne przenoszenie do wybranego folderu
• Pełna analiza i kategoryzacja plików
• Historia przenoszenia dla lepszych predykcji

🔧 DOSTĘPNE FUNKCJE:"""

        if USE_ENHANCED_ANALYZER:
            info_text += "\n✅ Zaawansowany analizator kategorii"
        if USE_ENHANCED_VISUALIZER:
            info_text += "\n✅ Rozszerzona wizualizacja grup"

        info_text += "\n\nProgram automatycznie tworzy logiczną strukturę folderów!"

        info_label = ttk.Label(info_frame, text=info_text, justify=tk.LEFT,
                               font=("Arial", 9), wraplength=500)
        info_label.pack(pady=(0, 15))

        # Ramka dolna
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

    # Konfiguracja interfejsu użytkownika
    setup_enhanced_ui_with_auto_organize(root)

    # Uruchomienie głównej pętli aplikacji
    root.mainloop()


if __name__ == "__main__":
    try:
        print("🗂️ Uruchamianie systemu organizacji plików z automatycznym tworzeniem folderów...")
        main()
    except Exception as e:
        print(f"Wystąpił krytyczny błąd: {e}")
        traceback.print_exc()
        try:
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror("Krytyczny błąd systemu", f"Wystąpił krytyczny błąd podczas uruchamiania:\n\n{str(e)}")
        except:
            pass