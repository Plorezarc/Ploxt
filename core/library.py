"""
Local audio library scanning helpers.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


AUDIO_EXTENSIONS = {".mp3", ".opus", ".flac", ".ogg", ".m4a", ".wav"}


@dataclass(frozen=True)
class AudioFile:
    path: Path
    title: str
    ext: str
    size_bytes: int
    modified_ts: float

    @property
    def size_str(self) -> str:
        if self.size_bytes >= 1_073_741_824:
            return f"{self.size_bytes / 1_073_741_824:.2f} GB"
        if self.size_bytes >= 1_048_576:
            return f"{self.size_bytes / 1_048_576:.1f} MB"
        if self.size_bytes >= 1024:
            return f"{self.size_bytes / 1024:.1f} KB"
        return f"{self.size_bytes} B"


def scan_audio_files(folder: str | Path) -> list[AudioFile]:
    root = Path(folder).expanduser()
    if not root.exists() or not root.is_dir():
        return []

    files: list[AudioFile] = []
    for path in root.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in AUDIO_EXTENSIONS:
            continue
        try:
            stat = path.stat()
        except OSError:
            continue
        files.append(
            AudioFile(
                path=path,
                title=path.stem,
                ext=path.suffix.lower().lstrip(".").upper(),
                size_bytes=stat.st_size,
                modified_ts=stat.st_mtime,
            )
        )
    return sorted(files, key=lambda item: item.modified_ts, reverse=True)
