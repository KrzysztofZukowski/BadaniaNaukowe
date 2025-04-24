# file_operations.py (fragment importów)
import os
import shutil
import tkinter as tk
from tkinter import filedialog, messagebox
import time
import stat
from datetime import datetime

# Upewnij się, że te importy są dostępne
try:
    from models import FileInfo
    from file_analyzer import get_mime_type, get_file_signature, extract_keywords, analyze_headers
except ImportError as e:
    print(f"Błąd importu modułów: {e}")
    # Możesz stworzyć prowizoryczne funkcje zastępcze, jeśli to konieczne