"""
core/settings.py
─────────────────────────────────────────────────────────────────────────────
User-configurable settings, persisted as JSON.

Defaults mirror what Ploxt ships with out-of-the-box.
"""

from __future__ import annotations

import json
from pathlib import Path
from core.history import DATA_DIR

SETTINGS_FILE: Path = DATA_DIR / "settings.json"

DEFAULTS: dict = {
    # ── Paths ──────────────────────────────────────────────────────────────
    "download_dir"       : str(Path.home() / "Downloads" / "Ploxt"),

    # ── Network ────────────────────────────────────────────────────────────
    "proxy"              : "",

    # ── Appearance ─────────────────────────────────────────────────────────
    "theme_mode"         : "dark",           # "dark" | "light"

    # ── Format defaults ────────────────────────────────────────────────────
    "default_format"     : "bestvideo+bestaudio/best",

    # ── ffmpeg ─────────────────────────────────────────────────────────────
    "ffmpeg_location"    : "",               # empty = auto-detect from PATH

    # ── Behaviour ──────────────────────────────────────────────────────────
    "open_folder_after"  : True,
    "concurrent_max"     : 3,
}


class AppSettings:
    """Simple dict-backed settings object with automatic persistence."""

    def __init__(self, path: Path = SETTINGS_FILE) -> None:
        self._path = path
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._data: dict = {**DEFAULTS}
        self._load()

    # ── Private ──────────────────────────────────────────────────────────────

    def _load(self) -> None:
        if self._path.exists():
            try:
                saved = json.loads(self._path.read_text(encoding="utf-8"))
                self._data.update(saved)
            except Exception:
                pass

    def _save(self) -> None:
        self._path.write_text(
            json.dumps(self._data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    # ── Public API ────────────────────────────────────────────────────────────

    def get(self, key: str, default=None):
        return self._data.get(key, default)

    def set(self, key: str, value) -> None:
        self._data[key] = value
        self._save()

    def all(self) -> dict:
        return dict(self._data)
