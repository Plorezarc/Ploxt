"""
core/history.py
─────────────────────────────────────────────────────────────────────────────
Persistent download history stored as a JSON file in the user's app-data dir.

Each record:
  {
      "id"        : str (uuid4),
      "title"     : str,
      "url"       : str,
      "format"    : str,
      "out_path"  : str,
      "timestamp" : ISO-8601 string,
      "status"    : "completed" | "failed"
  }
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


# ─────────────────────────────── Paths ───────────────────────────────────────

def _default_data_dir() -> Path:
    import sys, os
    if sys.platform == "win32":
        base = Path(os.environ.get("APPDATA", Path.home()))
    elif sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support"
    else:
        base = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))
    return base / "PloxtDesktop"


DATA_DIR   : Path = _default_data_dir()
HISTORY_FILE: Path = DATA_DIR / "history.json"


# ─────────────────────────────── HistoryManager ──────────────────────────────

class HistoryManager:
    """Thread-safe (GIL is sufficient) JSON-backed download history."""

    def __init__(self, path: Path = HISTORY_FILE) -> None:
        self._path = path
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._records: list[dict] = self._load()

    # ── Persistence ──────────────────────────────────────────────────────────

    def _load(self) -> list[dict]:
        if self._path.exists():
            try:
                return json.loads(self._path.read_text(encoding="utf-8"))
            except Exception:
                return []
        return []

    def _save(self) -> None:
        self._path.write_text(
            json.dumps(self._records, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    # ── Public API ────────────────────────────────────────────────────────────

    def add(
        self,
        title    : str,
        url      : str,
        fmt      : str,
        out_path : str,
        status   : str = "completed",
    ) -> str:
        record = {
            "id"        : str(uuid.uuid4()),
            "title"     : title,
            "url"       : url,
            "format"    : fmt,
            "out_path"  : out_path,
            "timestamp" : datetime.now(timezone.utc).isoformat(),
            "status"    : status,
        }
        self._records.insert(0, record)   # newest first
        self._save()
        return record["id"]

    def all(self) -> list[dict]:
        return list(self._records)

    def clear(self) -> None:
        self._records = []
        self._save()

    def remove(self, record_id: str) -> None:
        self._records = [r for r in self._records if r["id"] != record_id]
        self._save()

    def count(self) -> int:
        return len(self._records)
