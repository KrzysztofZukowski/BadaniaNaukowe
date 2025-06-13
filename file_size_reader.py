# file_size_reader.py
import os
import traceback
import subprocess
import platform


class FileSizeReader:

    @staticmethod
    def get_file_size(file_path):
        """Odczytuje rozmiar pliku używając wielu metod"""
        print(f"\n=== Próba odczytania rozmiaru pliku: {file_path} ===")

        # Najpierw spróbuj najprostszej i najbardziej niezawodnej metody
        try:
            size = os.path.getsize(file_path)
            if size > 0:
                print(f"Szybka metoda os.path.getsize zwróciła: {size} bajtów")
                return size
        except Exception as e:
            print(f"Szybka metoda nie powiodła się: {e}")

        # Jeśli szybka metoda zawiedzie, próbuj innych
        result = FileSizeReader._try_all_methods(file_path)

        if result['success']:
            print(f"Pomyślnie odczytano rozmiar: {result['size']} bajtów używając metody: {result['method']}")
            return result['size']
        else:
            # Ostateczna próba z blokiem try/except
            try:
                print("Ostateczna próba z os.stat...")
                file_stats = os.stat(file_path)
                size = file_stats.st_size
                print(f"Ostateczna próba zwróciła: {size} bajtów")
                return size
            except Exception as final_error:
                print(f"Wszystkie metody odczytu rozmiaru nie powiodły się: {final_error}")
                return 0

    @staticmethod
    def _try_all_methods(file_path):
        """Próbuje wszystkich dostępnych metod odczytu rozmiaru pliku"""
        methods = [
            FileSizeReader._try_os_stat,
            FileSizeReader._try_os_path_getsize,
            FileSizeReader._try_file_read,
            FileSizeReader._try_subprocess
        ]

        for method_func in methods:
            try:
                result = method_func(file_path)
                if result['success'] and result['size'] > 0:
                    return result
            except Exception as e:
                print(f"Metoda {method_func.__name__} niepowodzenie: {e}")
                traceback.print_exc()
                continue

        # Jeśli dotarliśmy tutaj, żadna metoda nie zadziałała
        return {'success': False, 'size': 0, 'method': 'none'}

    @staticmethod
    def _try_os_stat(file_path):

        print("Próba metody: os.stat")
        try:
            file_stats = os.stat(file_path)
            size = file_stats.st_size
            print(f"  os.stat zwrócił: {size} bajtów")
            return {'success': True, 'size': int(size), 'method': 'os.stat'}
        except Exception as e:
            print(f"  os.stat niepowodzenie: {e}")
            return {'success': False, 'size': 0, 'method': 'os.stat'}

    @staticmethod
    def _try_os_path_getsize(file_path):

        print("Próba metody: os.path.getsize")
        try:
            size = os.path.getsize(file_path)
            print(f"  os.path.getsize zwrócił: {size} bajtów")
            return {'success': True, 'size': int(size), 'method': 'os.path.getsize'}
        except Exception as e:
            print(f"  os.path.getsize niepowodzenie: {e}")
            return {'success': False, 'size': 0, 'method': 'os.path.getsize'}

    @staticmethod
    def _try_file_read(file_path):

        print("Próba metody: odczyt pliku")
        try:
            with open(file_path, 'rb') as f:
                f.seek(0, 2)  # Przejdź do końca pliku
                size = f.tell()  # Pobierz pozycję (rozmiar)
                print(f"  odczyt pliku zwrócił: {size} bajtów")
                return {'success': True, 'size': int(size), 'method': 'file_read'}
        except Exception as e:
            print(f"  odczyt pliku niepowodzenie: {e}")
            return {'success': False, 'size': 0, 'method': 'file_read'}

    @staticmethod
    def _try_subprocess(file_path):

        print("Próba metody: polecenia systemowe")
        try:
            system = platform.system()
            if system == 'Windows':
                # Komenda dir na Windows
                cmd = ['cmd', '/c', f'dir "{file_path}" /a /-C']
                output = subprocess.check_output(cmd, shell=True, text=True)
                for line in output.splitlines():
                    if os.path.basename(file_path) in line:
                        # Typowe wyjście: "01.01.2023  12:00    123456 filename.ext"
                        parts = line.split()
                        for part in parts:
                            try:
                                size = int(part.replace(',', ''))
                                print(f"  komenda dir zwróciła: {size} bajtów")
                                return {'success': True, 'size': size, 'method': 'dir_command'}
                            except ValueError:
                                continue
            else:
                # Komenda ls -l na Unix/Linux/Mac
                cmd = ['ls', '-l', file_path]
                output = subprocess.check_output(cmd, text=True)
                # Typowe wyjście: "-rw-r--r-- 1 user group 123456 date time filename"
                parts = output.split()
                if len(parts) >= 5:
                    try:
                        size = int(parts[4])
                        print(f"  komenda ls zwróciła: {size} bajtów")
                        return {'success': True, 'size': size, 'method': 'ls_command'}
                    except ValueError:
                        pass

            print("  nie udało się odczytać rozmiaru z polecenia systemowego")
            return {'success': False, 'size': 0, 'method': 'subprocess'}
        except Exception as e:
            print(f"  polecenie systemowe niepowodzenie: {e}")
            return {'success': False, 'size': 0, 'method': 'subprocess'}

    @staticmethod
    def format_size(size_in_bytes):
        """Formatuje rozmiar w bajtach na bardziej czytelną formę"""
        try:
            # Upewniamy się, że size_in_bytes jest liczbą
            size_in_bytes = int(size_in_bytes)

            if size_in_bytes < 1024:
                return f"{size_in_bytes} B"
            elif size_in_bytes < 1024 * 1024:
                return f"{size_in_bytes / 1024:.2f} KB"
            elif size_in_bytes < 1024 * 1024 * 1024:
                return f"{size_in_bytes / (1024 * 1024):.2f} MB"
            else:
                return f"{size_in_bytes / (1024 * 1024 * 1024):.2f} GB"
        except (ValueError, TypeError) as e:
            print(f"Błąd formatowania rozmiaru: {e}, wartość: {size_in_bytes}")
            if size_in_bytes == 0 or size_in_bytes is None:
                return "0 B"
            return "Błąd rozmiaru"