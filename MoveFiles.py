import os
import shutil
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from datetime import datetime


class FileInfo:
    """Klasa przechowująca informacje o przeniesionym pliku"""

    def __init__(self, name, extension, source_path, destination_path, status):
        self.name = name
        self.extension = extension
        self.source_path = source_path
        self.destination_path = destination_path
        self.status = status
        self.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def select_files():
    """Funkcja otwierająca okno dialogowe do wyboru plików"""
    root = tk.Tk()
    root.withdraw()  # Ukrycie głównego okna tkinter
    files = filedialog.askopenfilenames(
        title="Wybierz pliki do przeniesienia",
        filetypes=(("Wszystkie pliki", "*.*"),)
    )
    return files if files else []


def select_destination():
    """Funkcja otwierająca okno dialogowe do wyboru folderu docelowego"""
    root = tk.Tk()
    root.withdraw()  # Ukrycie głównego okna tkinter
    folder = filedialog.askdirectory(
        title="Wybierz folder docelowy"
    )
    return folder


def move_files(files, destination):
    """Funkcja przenosząca wybrane pliki do wskazanego folderu"""
    if not os.path.exists(destination):
        os.makedirs(destination)

    files_info = []

    for file_path in files:
        try:
            file_name = os.path.basename(file_path)
            name, extension = os.path.splitext(file_name)
            destination_path = os.path.join(destination, file_name)

            # Sprawdzenie, czy plik już istnieje w folderze docelowym
            if os.path.exists(destination_path):
                response = messagebox.askyesno(
                    "Plik już istnieje",
                    f"Plik {file_name} już istnieje w folderze docelowym. Czy chcesz go zastąpić?"
                )
                if not response:
                    files_info.append(FileInfo(name, extension, file_path, "", "Pominięto"))
                    continue

            shutil.move(file_path, destination_path)
            files_info.append(FileInfo(name, extension, file_path, destination_path, "Przeniesiono"))
        except Exception as e:
            files_info.append(FileInfo(
                os.path.splitext(os.path.basename(file_path))[0],
                os.path.splitext(os.path.basename(file_path))[1],
                file_path,
                "",
                f"Błąd: {str(e)}"
            ))
            print(f"Błąd podczas przenoszenia pliku {file_path}: {e}")

    return files_info


def show_files_table(files_info):
    """Funkcja wyświetlająca tabelę z informacjami o przeniesionych plikach"""
    if not files_info:
        messagebox.showinfo("Informacja", "Brak informacji o plikach do wyświetlenia.")
        return

    # Utworzenie nowego okna dla tabeli
    table_window = tk.Toplevel()
    table_window.title("Informacje o przeniesionych plikach")
    table_window.geometry("800x400")

    # Utworzenie ramki dla tabeli
    frame = tk.Frame(table_window)
    frame.pack(fill="both", expand=True, padx=10, pady=10)

    # Utworzenie tabeli
    columns = ("Nazwa", "Rozszerzenie", "Status", "Czas operacji")
    tree = ttk.Treeview(frame, columns=columns, show="headings")

    # Definicja nagłówków kolumn
    for col in columns:
        tree.heading(col, text=col)
        tree.column(col, width=150)

    # Dodanie danych do tabeli
    for file_info in files_info:
        tree.insert("", "end", values=(
            file_info.name,
            file_info.extension,
            file_info.status,
            file_info.timestamp
        ))

    # Dodanie paska przewijania
    scrollbar = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=scrollbar.set)
    scrollbar.pack(side="right", fill="y")
    tree.pack(fill="both", expand=True)

    # Przycisk do eksportu danych
    export_button = tk.Button(
        table_window,
        text="Eksportuj do pliku CSV",
        command=lambda: export_to_csv(files_info)
    )
    export_button.pack(pady=10)


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
            f.write("Nazwa,Rozszerzenie,Ścieżka źródłowa,Ścieżka docelowa,Status,Czas operacji\n")

            # Dane
            for file_info in files_info:
                f.write(f'"{file_info.name}","{file_info.extension}","{file_info.source_path}",' +
                        f'"{file_info.destination_path}","{file_info.status}","{file_info.timestamp}"\n')

        messagebox.showinfo("Sukces", f"Dane zostały pomyślnie wyeksportowane do {file_path}")
    except Exception as e:
        messagebox.showerror("Błąd", f"Wystąpił błąd podczas eksportu danych: {e}")


def main():
    # Utworzenie głównego okna
    root = tk.Tk()
    root.title("Przenoszenie plików")
    root.geometry("400x200")

    # Etykieta informacyjna
    label = tk.Label(root, text="Program do przenoszenia plików", font=("Arial", 14))
    label.pack(pady=10)

    # Przycisk do wyboru plików
    select_files_button = tk.Button(
        root,
        text="Wybierz pliki do przeniesienia",
        command=lambda: start_moving_process(root)
    )
    select_files_button.pack(pady=10)

    # Przycisk zamknięcia
    close_button = tk.Button(
        root,
        text="Zamknij",
        command=root.destroy
    )
    close_button.pack(pady=10)

    # Zmienna do przechowywania informacji o plikach
    files_info_list = []

    # Funkcja do obsługi procesu przenoszenia
    def start_moving_process(root):
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

    # Uruchomienie głównej pętli aplikacji
    root.mainloop()


if __name__ == "__main__":
    main()