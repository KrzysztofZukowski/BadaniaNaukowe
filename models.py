# models.py
from datetime import datetime


class FileInfo:
    """Klasa przechowująca informacje o przeniesionym pliku"""

    def __init__(self, name, extension, source_path, destination_path, status,
                 file_size=0, creation_date="", modification_date="", attributes="",
                 mime_type="", file_signature="", keywords="", headers_info=""):
        self.name = name
        self.extension = extension
        self.source_path = source_path
        self.destination_path = destination_path
        self.status = status
        self.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Podstawowe metadane
        self.file_size = file_size  # rozmiar w bajtach
        self.creation_date = creation_date
        self.modification_date = modification_date
        self.attributes = attributes  # atrybuty pliku jako string

        # Zaawansowane metadane
        self.mime_type = mime_type
        self.file_signature = file_signature
        self.keywords = keywords
        self.headers_info = headers_info