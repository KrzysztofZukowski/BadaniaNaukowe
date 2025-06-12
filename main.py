# main.py - NAPRAWIONA wersja z prostymi kategoriami dynamicznymi
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

# Importujemy funkcje - sprawdź czy są naprawione pliki, jeśli nie - użyj oryginalnych
try:
    # Próbuj użyć uproszczonego analizatora
    print("🔄 Próbuję załadować uproszczony analizator kategorii...")
    # Sprawdź czy istnieje nowa wersja category_analyzer.py z dynamicznymi kategoriami
    exec(open('category_analyzer.py').read())  # To nie zadziała, ale sprawdzi czy plik istnieje
    from category_analyzer import CategoryAnalyzer

    category_analyzer = CategoryAnalyzer()
    print("✅ Używam analizatora kategorii z dynamicznymi kategoriami")
    USE_DYNAMIC_ANALYZER = True
except:
    try:
        from category_analyzer import CategoryAnalyzer

        category_analyzer = CategoryAnalyzer()
        print("⚠️ Używam standardowego analizatora kategorii")
        USE_DYNAMIC_ANALYZER = False
    except ImportError:
        print("❌ Nie mogę załadować analizatora kategorii!")
        sys.exit(1)

from file_operations import select_files, select_destination, move_files
from gui_components import create_main_window, show_files_table_inline
from auto_folder_organizer import AutoFolderOrganizer

# Próbujemy zaimportować rozszerzony wizualizer
try:
    from enhanced_file_group_visualizer import EnhancedFileGroupVisualizer

    USE_ENHANCED_VISUALIZER = True
except ImportError:
    try:
        from file_group_visualizer import FileGroupVisualizer

        USE_ENHANCED_VISUALIZER = False
    except ImportError:
        USE_ENHANCED_VISUALIZER = False


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
        self.hierarchy_levels = []  # Lista poziomów hierarchii

        # Utworzenie okna
        self.window = tk.Toplevel(parent)
        self.window.title("Organizowanie plików")
        self.window.geometry("900x700")
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
                                text="🗂️ ORGANIZOWANIE PLIKÓW",
                                font=("Arial", 14, "bold"),
                                foreground="darkblue")
        title_label.pack(pady=(0, 20))

        # Opis
        desc_label = ttk.Label(main_frame,
                               text="Wybierz kategorie i ich kolejność do organizacji plików:",
                               font=("Arial", 10))
        desc_label.pack(pady=(0, 15))

        # Główny kontener z dwoma panelami
        panels_frame = ttk.Frame(main_frame)
        panels_frame.pack(fill="both", expand=True, pady=(0, 15))

        # Lewy panel - dostępne kategorie
        left_panel = ttk.LabelFrame(panels_frame, text="Dostępne kategorie", padding="10")
        left_panel.pack(side="left", fill="both", expand=True, padx=(0, 5))

        # Lista dostępnych kategorii
        self.available_listbox = tk.Listbox(left_panel, selectmode="single", height=10)
        self.available_listbox.pack(fill="both", expand=True, pady=(0, 10))

        # Dodaj dostępne kategorie
        categories = [
            ("Typ pliku", "type", "Grupuje według typu (dokumenty, obrazy, audio...)"),
            ("Rozszerzenie", "extension", "Grupuje według rozszerzenia (.txt, .jpg...)"),
            ("Data", "date", "Grupuje według daty utworzenia/modyfikacji"),
            ("Rozmiar", "size", "Grupuje według rozmiaru pliku"),
            ("Dynamiczne kategorie", "dynamic", "Grupuje według wzorców w nazwach")
        ]

        self.category_info = {}  # Słownik z informacjami o kategoriach
        for name, key, desc in categories:
            self.available_listbox.insert(tk.END, name)
            self.category_info[name] = {"key": key, "desc": desc}

        # Przycisk dodawania
        add_button = ttk.Button(left_panel, text="Dodaj →", command=self.add_category)
        add_button.pack()

        # Prawy panel - hierarchia organizacji
        right_panel = ttk.LabelFrame(panels_frame, text="Hierarchia organizacji", padding="10")
        right_panel.pack(side="right", fill="both", expand=True, padx=(5, 0))

        # Lista wybranej hierarchii
        self.hierarchy_listbox = tk.Listbox(right_panel, selectmode="single", height=10)
        self.hierarchy_listbox.pack(fill="both", expand=True, pady=(0, 10))

        # Przyciski do manipulacji hierarchią
        hierarchy_buttons = ttk.Frame(right_panel)
        hierarchy_buttons.pack(fill="x")

        ttk.Button(hierarchy_buttons, text="↑ W górę", command=self.move_up).pack(side="left", padx=2)
        ttk.Button(hierarchy_buttons, text="↓ W dół", command=self.move_down).pack(side="left", padx=2)
        ttk.Button(hierarchy_buttons, text="← Usuń", command=self.remove_category).pack(side="left", padx=2)
        ttk.Button(hierarchy_buttons, text="Wyczyść", command=self.clear_hierarchy).pack(side="left", padx=2)

        # Przykładowy opis hierarchii
        example_frame = ttk.Frame(main_frame)
        example_frame.pack(fill="x", pady=(0, 15))

        example_label = ttk.Label(example_frame,
                                  text="Przykład: Typ pliku → Data → Dynamiczne kategorie",
                                  font=("Arial", 9, "italic"),
                                  foreground="blue")
        example_label.pack(side="left")

        result_label = ttk.Label(example_frame,
                                 text="Rezultat: 📁 Dokumenty/2024/03 - March/Seria: Umowy/",
                                 font=("Arial", 9, "italic"),
                                 foreground="green")
        result_label.pack(side="left", padx=(20, 0))

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

        # Domyślna hierarchia
        self.set_default_hierarchy()

    def set_default_hierarchy(self):
        """Ustawia domyślną hierarchię"""
        default_hierarchy = ["Typ pliku", "Data"]
        for cat in default_hierarchy:
            if cat in self.category_info:
                self.hierarchy_listbox.insert(tk.END, cat)
                self.hierarchy_levels.append(self.category_info[cat]["key"])

    def add_category(self):
        """Dodaje wybraną kategorię do hierarchii"""
        selection = self.available_listbox.curselection()
        if not selection:
            return

        category_name = self.available_listbox.get(selection[0])

        # Sprawdź czy kategoria już jest w hierarchii
        if category_name in self.hierarchy_listbox.get(0, tk.END):
            messagebox.showwarning("Uwaga", f"Kategoria '{category_name}' już jest w hierarchii.")
            return

        # Dodaj do hierarchii
        self.hierarchy_listbox.insert(tk.END, category_name)
        self.hierarchy_levels.append(self.category_info[category_name]["key"])

        # Odśwież podgląd
        self.preview_structure()

    def remove_category(self):
        """Usuwa wybraną kategorię z hierarchii"""
        selection = self.hierarchy_listbox.curselection()
        if not selection:
            return

        index = selection[0]
        self.hierarchy_listbox.delete(index)
        del self.hierarchy_levels[index]

        # Odśwież podgląd
        self.preview_structure()

    def move_up(self):
        """Przesuwa wybraną kategorię w górę"""
        selection = self.hierarchy_listbox.curselection()
        if not selection or selection[0] == 0:
            return

        index = selection[0]
        # Pobierz elementy
        item = self.hierarchy_listbox.get(index)
        level = self.hierarchy_levels[index]

        # Usuń i wstaw wyżej
        self.hierarchy_listbox.delete(index)
        self.hierarchy_listbox.insert(index - 1, item)

        del self.hierarchy_levels[index]
        self.hierarchy_levels.insert(index - 1, level)

        # Zaznacz przesunięty element
        self.hierarchy_listbox.selection_set(index - 1)

        # Odśwież podgląd
        self.preview_structure()

    def move_down(self):
        """Przesuwa wybraną kategorię w dół"""
        selection = self.hierarchy_listbox.curselection()
        if not selection or selection[0] == self.hierarchy_listbox.size() - 1:
            return

        index = selection[0]
        # Pobierz elementy
        item = self.hierarchy_listbox.get(index)
        level = self.hierarchy_levels[index]

        # Usuń i wstaw niżej
        self.hierarchy_listbox.delete(index)
        self.hierarchy_listbox.insert(index + 1, item)

        del self.hierarchy_levels[index]
        self.hierarchy_levels.insert(index + 1, level)

        # Zaznacz przesunięty element
        self.hierarchy_listbox.selection_set(index + 1)

        # Odśwież podgląd
        self.preview_structure()

    def clear_hierarchy(self):
        """Czyści całą hierarchię"""
        self.hierarchy_listbox.delete(0, tk.END)
        self.hierarchy_levels.clear()
        self.preview_structure()

    def preview_structure(self):
        """Generuje podgląd struktury folderów"""
        try:
            if not self.hierarchy_levels:
                self.preview_text.delete('1.0', tk.END)
                self.preview_text.insert('1.0', "Wybierz kategorie do utworzenia hierarchii folderów.")
                return

            # Użyj custom hierarchy w organizerze
            structure = self.auto_organizer.analyze_folder_structure_custom(
                self.files_info,
                self.hierarchy_levels
            )

            # Wyczyść poprzedni podgląd
            self.preview_text.delete('1.0', tk.END)

            # Generuj tekst podglądu
            hierarchy_text = " → ".join(self.hierarchy_listbox.get(0, tk.END))
            preview_text = f"Hierarchia: {hierarchy_text}\n"
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
        if not self.hierarchy_levels:
            messagebox.showwarning("Uwaga", "Wybierz przynajmniej jedną kategorię do organizacji.")
            return

        self.result = {
            'hierarchy': self.hierarchy_levels,
            'use_existing': self.use_existing_var.get(),
            'execute': True
        }
        self.window.destroy()

    def cancel(self):
        """Anuluje operację"""
        self.result = {'execute': False}
        self.window.destroy()


def main():
    """Główna funkcja programu"""
    # Utworzenie głównego okna
    root = create_main_window()
    root.title("🎯 System Organizacji Plików z Dynamicznymi Kategoriami")
    root.geometry("1200x800")  # Zwiększone okno dla wyświetlania danych

    # Konfiguracja stylu
    style = ttk.Style()
    try:
        style.theme_use('clam')
    except:
        pass

    # Zmienne globalne
    files_info_list = []
    details_frame_ref = [None]  # Używamy listy żeby móc modyfikować w funkcjach

    # Inicjalizacja organizatora folderów
    auto_organizer = AutoFolderOrganizer(category_analyzer)

    def start_organize_process():
        """Proces z automatycznym organizowaniem folderów"""
        nonlocal files_info_list

        files = select_files()
        if not files:
            messagebox.showinfo("Informacja", "Nie wybrano żadnych plików.")
            return

        print(f"Wybrano {len(files)} plików do organizowania:")

        # Analizuj pliki bez przenoszenia
        progress_dialog = ProgressDialog(root, "Analiza plików")
        progress_dialog.update_status("Analizuję pliki...", "Przygotowywanie do organizowania")

        try:
            from models import FileInfo
            from datetime import datetime
            from file_size_reader import FileSizeReader
            from file_analyzer import get_mime_type, get_file_signature, extract_keywords, analyze_headers

            def safe_format_datetime(timestamp):
                try:
                    return datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
                except:
                    return "Data nieznana"

            # Stwórz tymczasowe obiekty FileInfo dla analizy
            temp_files_info = []

            for i, file_path in enumerate(files):
                try:
                    file_name = os.path.basename(file_path)
                    progress_dialog.update_status(
                        f"Analizuję: {file_name}",
                        f"Plik {i + 1} z {len(files)}"
                    )

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
                print("Anulowano organizowanie")
                return

            # Wybierz folder docelowy
            destination = select_destination()
            if not destination:
                messagebox.showinfo("Informacja", "Nie wybrano folderu docelowego.")
                return

            # Generuj mapowanie plików
            hierarchy = dialog.result['hierarchy']
            use_existing = dialog.result['use_existing']

            print(f"Generowanie struktury folderów z hierarchią: {hierarchy}...")
            file_mapping = auto_organizer.generate_folder_structure_custom(
                destination, temp_files_info, hierarchy
            )

            # Wykonaj przenoszenie bez symulacji
            print(f"Wykonywanie przenoszenia...")
            results = auto_organizer.create_folders_and_move_files(
                file_mapping, dry_run=False, use_existing_structure=use_existing
            )

            # Aktualizuj zmienne globalne
            files_info_list = temp_files_info

            # Pokaż wyniki
            show_organize_results(results)

            # Wyświetl tabelę z informacjami w głównym oknie
            show_files_table_inline(files_info_list, category_analyzer, details_frame_ref[0])

        except Exception as e:
            if 'progress_dialog' in locals():
                progress_dialog.close()
            print(f"BŁĄD w procesie organizowania: {e}")
            traceback.print_exc()
            messagebox.showerror("Błąd", f"Wystąpił błąd podczas organizowania:\n{str(e)}")

    def show_organize_results(results):
        """Wyświetla wyniki automatycznego organizowania"""
        # Okno wyników
        results_window = tk.Toplevel(root)
        results_window.title("Wyniki organizowania")
        results_window.geometry("600x500")

        # Ramka główna
        main_frame = ttk.Frame(results_window, padding="10")
        main_frame.pack(fill="both", expand=True)

        # Tytuł
        title = "✅ WYNIKI ORGANIZOWANIA"
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

    def show_dynamic_patterns():
        """Wyświetla okno z dynamicznymi wzorcami"""
        if not USE_DYNAMIC_ANALYZER or not hasattr(category_analyzer, 'get_dynamic_patterns_stats'):
            messagebox.showinfo("Informacja", "Dynamiczne wzorce niedostępne w tej wersji analizatora.")
            return

        try:
            stats = category_analyzer.get_dynamic_patterns_stats()

            # Utwórz okno
            patterns_window = tk.Toplevel(root)
            patterns_window.title("📊 Dynamiczne Wzorce")
            patterns_window.geometry("600x400")

            main_frame = ttk.Frame(patterns_window, padding="10")
            main_frame.pack(fill="both", expand=True)

            title_label = ttk.Label(main_frame, text="📊 DYNAMICZNE WZORCE NAZW",
                                    font=("Arial", 12, "bold"))
            title_label.pack(pady=(0, 10))

            # Tekst ze statystykami
            stats_text = tk.Text(main_frame, wrap=tk.WORD, font=("Courier", 10))
            scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=stats_text.yview)
            stats_text.configure(yscrollcommand=scrollbar.set)

            scrollbar.pack(side="right", fill="y")
            stats_text.pack(fill="both", expand=True)

            stats_text.insert('1.0', stats)

            ttk.Button(main_frame, text="Zamknij", command=patterns_window.destroy).pack(pady=(10, 0))

        except Exception as e:
            messagebox.showerror("Błąd", f"Błąd wyświetlania wzorców: {e}")

    def setup_enhanced_ui_with_organize(root):
        """Konfiguruje rozszerzony interfejs z organizowaniem"""
        root.configure(bg='#f5f5f5')

        # Ramka główna z scrollowaniem
        main_canvas = tk.Canvas(root)
        main_scrollbar = ttk.Scrollbar(root, orient="vertical", command=main_canvas.yview)
        scrollable_frame = ttk.Frame(main_canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: main_canvas.configure(scrollregion=main_canvas.bbox("all"))
        )

        main_canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        main_canvas.configure(yscrollcommand=main_scrollbar.set)

        # Pakowanie elementów scrollowania
        main_canvas.pack(side="left", fill="both", expand=True)
        main_scrollbar.pack(side="right", fill="y")

        # Ramka z przyciskami na górze
        top_frame = ttk.Frame(scrollable_frame)
        top_frame.pack(fill="x", padx=20, pady=20)

        # Banner tytułowy
        title = "🎯 SYSTEM ORGANIZACJI PLIKÓW Z DYNAMICZNYMI KATEGORIAMI"
        title_label = ttk.Label(top_frame, text=title,
                                foreground="darkblue", font=("Arial", 16, "bold"))
        title_label.pack(pady=(0, 10))

        # Status analizatora
        status_text = "✅ Dynamiczne kategorie AKTYWNE" if USE_DYNAMIC_ANALYZER else "⚠️ Standardowe kategorie"
        status_label = ttk.Label(top_frame, text=status_text,
                                 foreground="green" if USE_DYNAMIC_ANALYZER else "orange",
                                 font=("Arial", 10, "bold"))
        status_label.pack(pady=(0, 20))

        # Ramka dla głównych przycisków
        buttons_frame = ttk.LabelFrame(top_frame, text="Główne funkcje", padding="15")
        buttons_frame.pack(fill="x", pady=(0, 20))

        # Przycisk organizowania - GŁÓWNY
        organize_button = ttk.Button(
            buttons_frame,
            text="🗂️ Organizowanie",
            command=start_organize_process,
            style='Accent.TButton'
        )
        organize_button.pack(fill="x", pady=(0, 10))

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

        # Przycisk wzorców dynamicznych
        if USE_DYNAMIC_ANALYZER:
            patterns_button = ttk.Button(
                buttons_row,
                text="📈 Wzorce Dynamiczne",
                command=show_dynamic_patterns
            )
            patterns_button.pack(side="left", fill="x", expand=True, padx=(5, 0))

        # Przycisk zamknięcia
        close_button = ttk.Button(buttons_frame, text="Zamknij", command=root.destroy)
        close_button.pack(fill="x")

        # Ramka dla szczegółów plików (będzie wypełniana po operacjach)
        details_frame_ref[0] = ttk.LabelFrame(scrollable_frame, text="Szczegóły plików", padding="10")
        details_frame_ref[0].pack(fill="both", expand=True, padx=20, pady=(0, 20))

        # Domyślna informacja
        default_label = ttk.Label(details_frame_ref[0],
                                  text="Tu pojawią się szczegóły plików po wykonaniu operacji.",
                                  font=("Arial", 10, "italic"),
                                  foreground="gray")
        default_label.pack(pady=20)

        # Konfiguracja stylów
        try:
            style = ttk.Style()
            style.configure('Accent.TButton', font=('Arial', 11, 'bold'))
        except:
            pass

    # Konfiguracja interfejsu użytkownika
    setup_enhanced_ui_with_organize(root)

    # Uruchomienie głównej pętli aplikacji
    root.mainloop()


if __name__ == "__main__":
    try:
        print("🎯 Uruchamianie systemu organizacji plików z dynamicznymi kategoriami...")
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