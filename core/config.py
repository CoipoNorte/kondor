import os
import sys

APP_NAME    = "KONDOR"
APP_VERSION = "6.0"

DANGEROUS_PATHS = [
    "c:\\", "c:\\windows", "c:\\program files", "c:\\users",
    "c:\\program files (x86)", "c:\\system32",
]

IGNORE_DIRS = {
    "node_modules", ".git", ".next", ".nuxt", "__pycache__",
    "dist", "build", ".cache", ".vite", "coverage",
    ".svelte-kit", ".output", "venv", "env", ".env",
}

IGNORE_FILES = {
    ".DS_Store", "Thumbs.db", "desktop.ini",
}

CONFIG_FILE = os.path.join(os.path.expanduser("~"), ".condor_config.json")


def find_file(filename: str) -> str | None:
    candidates = []
    if getattr(sys, "frozen", False):
        candidates.append(os.path.join(sys._MEIPASS, filename))
    script_dir = os.path.dirname(os.path.abspath(__file__))
    candidates.append(os.path.join(script_dir, "..", filename))
    candidates.append(os.path.join(os.getcwd(), filename))
    for p in candidates:
        norm = os.path.normpath(p)
        if os.path.isfile(norm):
            return norm
    return None


def load_txt(filename: str) -> str:
    path = find_file(filename)
    if path:
        try:
            with open(path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            print(f"[KONDOR] Error leyendo {filename}: {e}")
    return f"Error: {filename} no encontrado junto a condor.py"


def validate_path(path: str) -> bool:
    norm = os.path.normpath(path).lower()
    return not any(
        norm == os.path.normpath(d).lower() for d in DANGEROUS_PATHS)
