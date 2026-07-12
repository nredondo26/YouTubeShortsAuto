"""File utilities: temp cleanup, song management, URL building."""

import os
import random
import zipfile
import platform
import requests

from src.config import ROOT_DIR, MP_DIR, SONGS_DIR, get_zip_url, get_verbose
from src.constants import AUDIO_EXTENSIONS
from src.status import info, warning, error, success


def build_youtube_url(video_id: str) -> str:
    return f"https://www.youtube.com/watch?v={video_id}"


def rem_temp_files() -> None:
    """Remove all non-JSON files from .mp directory."""
    if not os.path.exists(MP_DIR):
        return
    for filename in os.listdir(MP_DIR):
        filepath = os.path.join(MP_DIR, filename)
        if os.path.isfile(filepath) and not filename.endswith(".json"):
            try:
                os.remove(filepath)
            except OSError:
                pass


def close_selenium_instances() -> None:
    """Kill any running Firefox instances (Selenium leftovers)."""
    try:
        if platform.system() == "Windows":
            os.system("taskkill /f /im firefox.exe >nul 2>&1")
        else:
            os.system("pkill firefox 2>/dev/null")
    except Exception:
        pass


def fetch_songs() -> None:
    """Download background music songs if not already present."""
    os.makedirs(SONGS_DIR, exist_ok=True)

    existing = [
        f for f in os.listdir(SONGS_DIR)
        if os.path.isfile(os.path.join(SONGS_DIR, f))
        and f.lower().endswith(AUDIO_EXTENSIONS)
    ]
    if existing:
        return

    configured_url = get_zip_url().strip()
    if not configured_url:
        warning("No zip_url configured for songs. Videos will have no background music.")
        return

    try:
        info("Downloading background music...")
        response = requests.get(configured_url, timeout=120)
        response.raise_for_status()

        archive_path = os.path.join(SONGS_DIR, "songs.zip")
        with open(archive_path, "wb") as f:
            f.write(response.content)

        SAFE_EXTENSIONS = AUDIO_EXTENSIONS + (".flac",)
        with zipfile.ZipFile(archive_path, "r") as zf:
            for member in zf.namelist():
                basename = os.path.basename(member)
                if not basename or not basename.lower().endswith(SAFE_EXTENSIONS):
                    continue
                if ".." in member or member.startswith("/"):
                    continue
                zf.extract(member, SONGS_DIR)

        os.remove(archive_path)
        success("Background music downloaded.")
    except Exception as e:
        error(f"Failed to download songs: {e}")


def choose_random_song() -> str | None:
    """Choose a random audio file from Songs/ or download free music."""
    from src.music import choose_random_song as _choose_random_song
    return _choose_random_song()
