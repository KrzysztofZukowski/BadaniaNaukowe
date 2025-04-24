# file_analyzer.py
import os
import mimetypes
import re
import json
import collections
from datetime import datetime

# Próbujemy zaimportować biblioteki, a jeśli nie są dostępne, tworzymy zastępcze funkcje
try:
    import magic
except ImportError:
    print("Biblioteka 'magic' nie jest zainstalowana. Używanie prostej detekcji MIME.")
    magic = None

try:
    from PIL import Image
    from PIL.ExifTags import TAGS
except ImportError:
    print("Biblioteka 'pillow' nie jest zainstalowana. Analiza obrazów będzie ograniczona.")
    Image = None

try:
    import PyPDF2
except ImportError:
    print("Biblioteka 'PyPDF2' nie jest zainstalowana. Analiza PDF będzie ograniczona.")
    PyPDF2 = None

try:
    import docx
except ImportError:
    print("Biblioteka 'python-docx' nie jest zainstalowana. Analiza DOCX będzie ograniczona.")
    docx = None

try:
    import mutagen
except ImportError:
    print("Biblioteka 'mutagen' nie jest zainstalowana. Analiza plików audio będzie ograniczona.")
    mutagen = None

# Słownik rozszerzeń do kategorii plików
FILE_CATEGORIES = {
    'image': ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp'],
    'document': ['.pdf', '.doc', '.docx', '.txt', '.rtf', '.odt'],
    'spreadsheet': ['.xls', '.xlsx', '.csv', '.ods'],
    'presentation': ['.ppt', '.pptx', '.odp'],
    'audio': ['.mp3', '.wav', '.flac', '.aac', '.ogg'],
    'video': ['.mp4', '.avi', '.mkv', '.mov', '.wmv'],
    'archive': ['.zip', '.rar', '.7z', '.tar', '.gz'],
    'code': ['.py', '.js', '.html', '.css', '.java', '.cpp', '.c', '.h']
}


def get_mime_type(file_path):
    """Pobiera typ MIME pliku"""
    try:
        if magic:
            mime_type = magic.Magic(mime=True).from_file(file_path)
            return mime_type
        else:
            # Prosta fallback metoda określania typu MIME na podstawie rozszerzenia
            mime_type, _ = mimetypes.guess_type(file_path)
            return mime_type or "application/octet-stream"
    except Exception as e:
        print(f"Błąd przy określaniu typu MIME: {e}")
        return "nieznany/nieznany"


def get_file_signature(file_path):
    """Pobiera sygnaturę pliku (magiczne bajty) do identyfikacji formatu"""
    try:
        # Pobieramy pierwsze 8 bajtów pliku jako sygnaturę
        with open(file_path, 'rb') as f:
            signature = f.read(8).hex().upper()

        # Słownik znanych sygnatur plików
        signatures = {
            'FFD8FF': 'JPEG',
            '89504E470D0A1A0A': 'PNG',
            '47494638': 'GIF',
            '25504446': 'PDF',
            '504B0304': 'ZIP/DOCX/XLSX',
            '4D546864': 'MIDI',
            '52494646': 'RIFF/WAV/AVI',
            '526172211A0700': 'RAR',
            '377ABCAF271C': '7Z',
            '0001000000': 'ICO',
            '7F454C46': 'ELF',
            '4D5A': 'EXE',
            '1F8B08': 'GZIP'
        }

        for sig, format_name in signatures.items():
            if signature.startswith(sig):
                return format_name

        return "Nieznana"
    except Exception as e:
        print(f"Błąd przy określaniu sygnatury pliku: {e}")
        return "Nie udało się określić"


def extract_keywords(file_path, max_keywords=5):
    """Ekstrahuje słowa kluczowe z pliku na podstawie jego typu"""
    try:
        mime_type = get_mime_type(file_path)
        text_content = ""

        # Pobieramy zawartość tekstową pliku w zależności od jego typu
        if 'text/' in mime_type:
            # Dla plików tekstowych
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    text_content = f.read()
            except:
                return "Nie udało się odczytać pliku tekstowego"
        elif 'application/pdf' in mime_type and PyPDF2:
            # Dla plików PDF
            try:
                with open(file_path, 'rb') as f:
                    pdf_reader = PyPDF2.PdfReader(f)
                    for page_num in range(min(3, len(pdf_reader.pages))):  # Analizujemy tylko kilka pierwszych stron
                        text_content += pdf_reader.pages[page_num].extract_text()
            except:
                return "Nie udało się przeanalizować pliku PDF"
        elif mime_type in ['application/vnd.openxmlformats-officedocument.wordprocessingml.document'] and docx:
            # Dla plików DOCX
            try:
                doc = docx.Document(file_path)
                for para in doc.paragraphs:
                    text_content += para.text + " "
            except:
                return "Nie udało się przeanalizować pliku DOCX"
        else:
            return "Typ pliku nie obsługuje analizy słów kluczowych"

        # Jeśli nie udało się pobrać treści
        if not text_content:
            return "Brak treści do analizy"

        # Analiza częstotliwości słów
        words = re.findall(r'\b[a-zA-Z0-9_żółćęśąźńŻÓŁĆĘŚĄŹŃ]{3,}\b', text_content.lower())

        # Usuwamy popularne słowa (stopwords)
        stopwords = {'and', 'the', 'to', 'of', 'a', 'in', 'is', 'it', 'you', 'that', 'was', 'for', 'on', 'are', 'with',
                     'as', 'this', 'nie', 'tak', 'to', 'jest', 'i', 'w', 'na', 'się', 'z', 'do', 'że'}
        filtered_words = [w for w in words if w not in stopwords]

        # Zliczamy wystąpienia słów
        counter = collections.Counter(filtered_words)

        # Zwracamy najczęściej występujące słowa jako słowa kluczowe
        keywords = [word for word, count in counter.most_common(max_keywords)]

        return ", ".join(keywords) if keywords else "Brak słów kluczowych"
    except Exception as e:
        print(f"Błąd przy ekstrakcji słów kluczowych: {e}")
        return "Nie udało się przeanalizować"


def analyze_headers(file_path):
    """Analizuje nagłówki plików graficznych, audio, wideo"""
    try:
        mime_type = get_mime_type(file_path)
        headers_info = {}

        # Analiza plików graficznych
        if 'image/' in mime_type and Image:
            try:
                with Image.open(file_path) as img:
                    headers_info['format'] = img.format
                    headers_info['mode'] = img.mode
                    headers_info['width'] = img.width
                    headers_info['height'] = img.height

                    # Próba uzyskania danych EXIF
                    exif_data = {}
                    if hasattr(img, '_getexif') and img._getexif():
                        for tag_id, value in img._getexif().items():
                            tag = TAGS.get(tag_id, tag_id)
                            exif_data[tag] = str(value)

                        # Wybieramy kilka ważnych informacji z EXIF
                        important_exif = ['Make', 'Model', 'DateTime', 'ExposureTime', 'FNumber', 'ISOSpeedRatings']
                        for tag in important_exif:
                            if tag in exif_data:
                                headers_info[tag] = exif_data[tag]
            except Exception as e:
                return f"Błąd analizy obrazu: {e}"

        # Analiza plików audio
        elif 'audio/' in mime_type and mutagen:
            try:
                audio = mutagen.File(file_path)
                if audio:
                    headers_info['length'] = f"{int(audio.info.length // 60)}:{int(audio.info.length % 60):02d}"
                    headers_info['bitrate'] = f"{audio.info.bitrate // 1000}kbps" if hasattr(audio.info,
                                                                                             'bitrate') else "N/A"
                    headers_info['sample_rate'] = f"{audio.info.sample_rate}Hz" if hasattr(audio.info,
                                                                                           'sample_rate') else "N/A"

                    # Pobieramy metadane (tagi)
                    if hasattr(audio, 'tags') and audio.tags:
                        for key in ['title', 'artist', 'album', 'genre']:
                            if key in audio:
                                headers_info[key] = str(audio[key][0])
            except Exception as e:
                return f"Błąd analizy audio: {e}"

        # Analiza plików wideo
        elif 'video/' in mime_type:
            # Tutaj możnaby użyć biblioteki jak ffmpeg-python, ale jest to bardziej zaawansowane
            # i może wymagać dodatkowych instalacji
            return "Analiza wideo wymaga dodatkowych bibliotek"

        # Formatowanie wyniku jako string
        if headers_info:
            return json.dumps(headers_info, ensure_ascii=False)
        else:
            return "Brak informacji o nagłówkach"

    except Exception as e:
        print(f"Błąd podczas analizy nagłówków: {e}")
        return "Nie udało się przeanalizować nagłówków"