"""
core/downloader.py
─────────────────────────────────────────────────────────────────────────────
yt-dlp integration layer.

Architecture
────────────
All yt-dlp work (info extraction + download) runs on daemon background
threads so the Tk main loop is never blocked.

Thread → UI communication uses a single thread-safe queue.Queue[dict].
The UI polls it on a 100 ms timer and dispatches payloads to registered
callback handlers.

Payload types (field "type"):
  "info"        — video metadata arrived (title, thumbnail_url, formats …)
  "progress"    — download progress update
  "finished"    — download completed successfully
  "error"       — any exception that occurred on the worker thread
  "log"         — informational log line from yt-dlp's logger
"""

from __future__ import annotations

import threading
import queue
import re
from dataclasses import dataclass, field
from typing import Callable, Optional
from pathlib import Path
import time

# yt-dlp is an optional runtime dependency; we guard the import so the UI
# can still render an install-prompt if the library is missing.
try:
    import yt_dlp                                   # type: ignore
    YDL_AVAILABLE = True
except ImportError:
    YDL_AVAILABLE = False


# ─────────────────────────────── Data Models ─────────────────────────────────

@dataclass
class VideoFormat:
    """A single downloadable format entry from yt-dlp."""
    format_id  : str
    ext        : str
    resolution : str    # "1920x1080", "audio only", …
    fps        : Optional[int]
    vcodec     : str
    acodec     : str
    filesize   : Optional[int]
    tbr        : Optional[float]   # total bitrate kbps
    note       : str               # yt-dlp's human-readable format note

    @property
    def is_audio_only(self) -> bool:
        return self.vcodec in ("none", "", None)

    @property
    def label(self) -> str:
        """Short label shown in the UI quality selector."""
        if self.is_audio_only:
            return f"Audio - {self.ext.upper()}  {self.note}"
        res = self.resolution.split("x")[-1] if "x" in self.resolution else self.resolution
        return f"{res}p  {self.ext.upper()}  {self.note}"

    @property
    def size_str(self) -> str:
        if self.filesize:
            mb = self.filesize / 1_048_576
            return f"{mb:.1f} MB"
        return "? MB"


@dataclass
class VideoInfo:
    """Normalised metadata returned after extract_info."""
    url           : str
    title         : str
    uploader      : str
    duration      : int              # seconds
    thumbnail_url : Optional[str]
    view_count    : Optional[int]
    upload_date   : Optional[str]
    formats       : list[VideoFormat] = field(default_factory=list)
    raw           : dict             = field(default_factory=dict)

    @property
    def duration_str(self) -> str:
        m, s = divmod(self.duration, 60)
        h, m = divmod(m, 60)
        return f"{h:02d}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"

    @property
    def best_formats(self) -> list[VideoFormat]:
        """
        Returns a curated list for the quality selector:
          Best (auto-merge), common resolutions, Audio Only.
        """
        seen_res: set[str] = set()
        curated: list[VideoFormat] = []

        # 1. Add a "Best (auto)" pseudo-entry — handled by format string "bestvideo+bestaudio"
        curated.append(VideoFormat(
            format_id="bestvideo+bestaudio/best",
            ext="mp4", resolution="Best (auto)",
            fps=None, vcodec="auto", acodec="auto",
            filesize=None, tbr=None, note="Highest quality"
        ))

        # 2. Real video formats — pick best per resolution
        video_fmts = sorted(
            [f for f in self.formats if not f.is_audio_only and f.resolution not in ("none", "")],
            key=lambda f: (-(f.tbr or 0))
        )
        for fmt in video_fmts:
            if fmt.resolution not in seen_res:
                seen_res.add(fmt.resolution)
                curated.append(fmt)

        # 3. Audio-only options
        audio_fmts = sorted(
            [f for f in self.formats if f.is_audio_only],
            key=lambda f: -(f.tbr or 0)
        )
        if audio_fmts:
            # Best audio
            curated.append(VideoFormat(
                format_id="bestaudio/best",
                ext="mp3", resolution="audio only",
                fps=None, vcodec="none", acodec="auto",
                filesize=None, tbr=None, note="Best audio"
            ))
            # Also expose individual audio formats
            for af in audio_fmts[:3]:
                curated.append(af)

        return curated


# ─────────────────────────────── Logger ──────────────────────────────────────

class _QueueLogger:
    """Feeds yt-dlp log output into the shared event queue."""

    def __init__(self, q: queue.Queue) -> None:
        self._q = q

    def debug(self, msg: str) -> None:
        # yt-dlp sends progress lines through debug(); filter them out here
        # (they also come through progress_hook)
        if msg.startswith("[download]"):
            return
        self._q.put({"type": "log", "level": "debug", "text": msg})

    def info(self, msg: str) -> None:
        self._q.put({"type": "log", "level": "info", "text": msg})

    def warning(self, msg: str) -> None:
        self._q.put({"type": "log", "level": "warning", "text": msg})

    def error(self, msg: str) -> None:
        self._q.put({"type": "log", "level": "error", "text": msg})


# ─────────────────────────────── Worker Threads ──────────────────────────────

def _extract_worker(url: str, q: queue.Queue, proxy: Optional[str] = None) -> None:
    """
    Background thread: extract video metadata without downloading.
    Posts a single "info" or "error" payload to q.
    """
    if not YDL_AVAILABLE:
        q.put({"type": "error", "message": "yt-dlp is not installed.\nRun:  pip install yt-dlp"})
        return

    ydl_opts = {
        "quiet": True,
        "no_warnings": False,
        "logger": _QueueLogger(q),
        "skip_download": True,
    }
    if proxy:
        ydl_opts["proxy"] = proxy

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            raw = ydl.extract_info(url, download=False)

        if raw is None:
            q.put({"type": "error", "message": "No information returned by yt-dlp."})
            return

        # ── Parse formats ────────────────────────────────────────────────────
        formats: list[VideoFormat] = []
        for f in raw.get("formats", []):
            formats.append(VideoFormat(
                format_id  = f.get("format_id", ""),
                ext        = f.get("ext", ""),
                resolution = f.get("resolution", ""),
                fps        = f.get("fps"),
                vcodec     = f.get("vcodec", "none"),
                acodec     = f.get("acodec", "none"),
                filesize   = f.get("filesize") or f.get("filesize_approx"),
                tbr        = f.get("tbr"),
                note       = f.get("format_note", ""),
            ))

        info = VideoInfo(
            url           = url,
            title         = raw.get("title", "Unknown Title"),
            uploader      = raw.get("uploader", "Unknown"),
            duration      = raw.get("duration") or 0,
            thumbnail_url = raw.get("thumbnail"),
            view_count    = raw.get("view_count"),
            upload_date   = raw.get("upload_date"),
            formats       = formats,
            raw           = raw,
        )
        q.put({"type": "info", "data": info})

    except Exception as exc:
        q.put({"type": "error", "message": str(exc)})


def _download_worker(
    info     : VideoInfo,
    fmt_id   : str,
    out_dir  : Path,
    q        : queue.Queue,
    proxy    : Optional[str] = None,
    audio_codec: str = "mp3",
) -> None:
    """
    Background thread: download a specific format and report progress.
    """
    if not YDL_AVAILABLE:
        q.put({"type": "error", "message": "yt-dlp is not installed."})
        return

    audio_codec = audio_codec.lower()
    if audio_codec not in {"mp3", "opus", "flac"}:
        audio_codec = "mp3"

    downloaded_path: Optional[Path] = None

    def progress_hook(d: dict) -> None:
        status = d.get("status", "")

        if status == "downloading":
            # ── Calculate percentage ─────────────────────────────────────────
            pct_str = d.get("_percent_str", "").strip().replace("%", "")
            try:
                percent = float(pct_str)
            except (ValueError, TypeError):
                downloaded = d.get("downloaded_bytes") or 0
                total      = d.get("total_bytes") or d.get("total_bytes_estimate") or 1
                percent    = (downloaded / total) * 100

            # ── Speed ────────────────────────────────────────────────────────
            speed_str = d.get("_speed_str", "").strip() or "-- B/s"
            speed_str = re.sub(r"\x1b\[[0-9;]*m", "", speed_str)  # strip ANSI

            # ── ETA ──────────────────────────────────────────────────────────
            eta_str = d.get("_eta_str", "").strip() or "--:--"
            eta_str = re.sub(r"\x1b\[[0-9;]*m", "", eta_str)

            # ── Size strings ─────────────────────────────────────────────────
            downloaded_bytes = d.get("downloaded_bytes") or 0
            total_bytes      = d.get("total_bytes") or d.get("total_bytes_estimate") or 0

            def fmt_bytes(b: int) -> str:
                if b >= 1_073_741_824:
                    return f"{b/1_073_741_824:.2f} GB"
                if b >= 1_048_576:
                    return f"{b/1_048_576:.1f} MB"
                if b >= 1024:
                    return f"{b/1024:.1f} KB"
                return f"{b} B"

            q.put({
                "type"       : "progress",
                "percent"    : min(percent, 100.0),
                "speed"      : speed_str,
                "eta"        : eta_str,
                "downloaded" : fmt_bytes(downloaded_bytes),
                "total"      : fmt_bytes(total_bytes),
                "filename"   : d.get("filename", ""),
            })

        elif status == "finished":
            q.put({"type": "progress", "percent": 100.0,
                   "speed": "", "eta": "Done", "downloaded": "", "total": "",
                   "filename": d.get("filename", "")})

    def postprocessor_hook(d: dict) -> None:
        nonlocal downloaded_path
        if d.get("status") != "finished":
            return

        info_dict = d.get("info_dict") or {}
        filepath = d.get("filepath") or info_dict.get("filepath") or info_dict.get("_filename")
        if filepath:
            downloaded_path = Path(filepath)

    # ── Build ydl_opts ───────────────────────────────────────────────────────
    outtmpl = str(out_dir / "%(title)s.%(ext)s")

    # Translate our pseudo format IDs to real yt-dlp format strings
    if fmt_id in ("bestvideo+bestaudio/best", "best"):
        fmt_str = "bestvideo+bestaudio/best"
    elif fmt_id in ("bestaudio/best",):
        fmt_str = "bestaudio/best"
    else:
        # For a real format_id, also grab best audio and merge
        fmt_str = f"{fmt_id}+bestaudio/{fmt_id}/best"

    selected_format = next((f for f in info.formats if f.format_id == fmt_id), None)
    is_audio_request = "audio" in fmt_id or bool(selected_format and selected_format.is_audio_only)

    ydl_opts = {
        "format"          : fmt_str,
        "outtmpl"         : outtmpl,
        "progress_hooks"  : [progress_hook],
        "postprocessor_hooks": [postprocessor_hook],
        "logger"          : _QueueLogger(q),
        "quiet"           : True,
        "no_warnings"     : False,
        "merge_output_format": "mp4",
        "postprocessors"  : [{
            "key"            : "FFmpegVideoConvertor",
            "preferedformat" : "mp4",
        }] if not is_audio_request else [],
    }

    # Audio-only: convert to the selected codec.
    if is_audio_request:
        audio_pp = {
            "key"            : "FFmpegExtractAudio",
            "preferredcodec" : audio_codec,
        }
        if audio_codec == "mp3":
            audio_pp["preferredquality"] = "320"
        ydl_opts["postprocessors"] = [audio_pp]
        ydl_opts.pop("merge_output_format", None)

    if proxy:
        ydl_opts["proxy"] = proxy

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            expected_path = Path(ydl.prepare_filename(info.raw))
            expected_path = expected_path.with_suffix(f".{audio_codec}" if is_audio_request else ".mp4")
            ydl.download([info.url])

        if downloaded_path is None and expected_path.exists():
            downloaded_path = expected_path

        q.put({
            "type": "finished",
            "title": info.title,
            "out_dir": str(out_dir),
            "filepath": str(downloaded_path) if downloaded_path else "",
        })

    except Exception as exc:
        q.put({"type": "error", "message": str(exc)})


# ─────────────────────────────── Public API ──────────────────────────────────

class DownloadManager:
    """
    High-level controller used by the UI layer.

    Usage
    ─────
    mgr = DownloadManager(event_callback=my_handler)
    mgr.fetch_info("https://youtu.be/xyz")
    mgr.start_download(video_info, format_id, Path("~/Downloads"))

    The event_callback receives dict payloads (see module docstring).
    It is always invoked on the Tk main thread via root.after().
    """

    def __init__(
        self,
        event_callback: Callable[[dict], None],
        root,           # ctk.CTk instance for thread-safe after()
        proxy: Optional[str] = None,
    ) -> None:
        self._cb    = event_callback
        self._root  = root
        self._proxy = proxy
        self._q: queue.Queue = queue.Queue()
        self._active_threads: list[threading.Thread] = []

        # Start the polling loop
        self._poll()

    # ── Public methods ────────────────────────────────────────────────────────

    def fetch_info(self, url: str) -> None:
        """Spawn a background thread to extract video metadata."""
        t = threading.Thread(
            target=_extract_worker,
            args=(url, self._q, self._proxy),
            daemon=True,
            name=f"ploxt-info-{int(time.time())}",
        )
        t.start()
        self._active_threads.append(t)

    def start_download(
        self,
        info    : VideoInfo,
        fmt_id  : str,
        out_dir : Path,
        audio_codec: str = "mp3",
    ) -> None:
        """Spawn a background thread to download the chosen format."""
        out_dir.mkdir(parents=True, exist_ok=True)
        t = threading.Thread(
            target=_download_worker,
            args=(info, fmt_id, out_dir, self._q, self._proxy, audio_codec),
            daemon=True,
            name=f"ploxt-dl-{int(time.time())}",
        )
        t.start()
        self._active_threads.append(t)

    def set_proxy(self, proxy: Optional[str]) -> None:
        self._proxy = proxy

    # ── Internal: queue polling ───────────────────────────────────────────────

    def _poll(self) -> None:
        """
        Drain the event queue on the main Tk thread every 80 ms.
        This is the bridge between worker threads and the UI.
        """
        try:
            while True:
                payload = self._q.get_nowait()
                self._cb(payload)
        except queue.Empty:
            pass
        finally:
            # Reschedule ourselves
            self._root.after(80, self._poll)
