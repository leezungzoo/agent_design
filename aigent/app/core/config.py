from __future__ import annotations

from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
ROOT_DIR = APP_DIR.parent

DATA_DIR = ROOT_DIR / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
FC26_CSV = RAW_DATA_DIR / "FC26_20250921.csv"
SQUAD_DATA_DIR = DATA_DIR / "squads"
SQUAD_SAVE_FILE = SQUAD_DATA_DIR / "squads.json"

STATIC_DIR = APP_DIR / "static"
TEMPLATES_DIR = APP_DIR / "templates"
PLAYER_IMAGE_DIR = STATIC_DIR / "images" / "players"
ENV_PATH = ROOT_DIR / ".env"
