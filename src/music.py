"""Music module - free background music for videos."""

import os
import sys
import random
from typing import Optional

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

MUSIC_DIR = os.path.join(ROOT_DIR, ".mp", "music")
os.makedirs(MUSIC_DIR, exist_ok=True)

AUDIO_EXTENSIONS = (".mp3", ".wav", ".ogg", ".m4a")


def choose_random_song() -> Optional[str]:
    """Choose a random audio file from Songs/ directory.
    
    Returns None if no local songs found (music is optional).
    """
    from src.config import MP_DIR as _MP_DIR
    songs_dir = os.path.join(_MP_DIR, "Songs")

    if os.path.exists(songs_dir):
        songs = [
            f for f in os.listdir(songs_dir)
            if os.path.isfile(os.path.join(songs_dir, f))
            and f.lower().endswith(AUDIO_EXTENSIONS)
        ]
        if songs:
            return os.path.join(songs_dir, random.choice(songs))

    return None


def list_genres() -> list:
    """List available music genres."""
    return []


def get_local_songs() -> list:
    """Get list of local songs in Songs/ directory."""
    from src.config import MP_DIR as _MP_DIR
    songs_dir = os.path.join(_MP_DIR, "Songs")

    if not os.path.exists(songs_dir):
        return []

    return [
        f for f in os.listdir(songs_dir)
        if os.path.isfile(os.path.join(songs_dir, f))
        and f.lower().endswith(AUDIO_EXTENSIONS)
    ]


if __name__ == "__main__":
    print("Local songs:", get_local_songs())
