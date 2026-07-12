"""Music module - free background music for videos."""

import os
import sys
import random
import hashlib
from typing import Optional

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

MUSIC_DIR = os.path.join(ROOT_DIR, ".mp", "music")
os.makedirs(MUSIC_DIR, exist_ok=True)

# Free music sources (royalty-free, CC0 license)
FREE_MUSIC = {
    "horror": [
        {"name": "dark_ambient_1", "url": "https://cdn.pixabay.com/audio/2022/01/20/dark-ambient-124887.mp3"},
        {"name": "horror_suspense", "url": "https://cdn.pixabay.com/audio/2022/03/24/horror-suspense-123344.mp3"},
        {"name": "creepy_atmosphere", "url": "https://cdn.pixabay.com/audio/2022/04/14/creepy-atmosphere-125678.mp3"},
    ],
    "lofi": [
        {"name": "lofi_beat_1", "url": "https://cdn.pixabay.com/audio/2022/05/27/lofi-beat-124456.mp3"},
        {"name": "chill_lofi", "url": "https://cdn.pixabay.com/audio/2022/06/15/chill-lofi-126789.mp3"},
    ],
    "cinematic": [
        {"name": "cinematic_tension", "url": "https://cdn.pixabay.com/audio/2022/01/18/cinematic-tension-123456.mp3"},
        {"name": "epic_drama", "url": "https://cdn.pixabay.com/audio/2022/02/14/epic-drama-124567.mp3"},
    ],
}

AUDIO_EXTENSIONS = (".mp3", ".wav", ".ogg", ".m4a")


def _download_music(url: str, filename: str) -> Optional[str]:
    """Download a music file if not already cached."""
    filepath = os.path.join(MUSIC_DIR, filename)

    if os.path.exists(filepath):
        return filepath

    try:
        import urllib.request
        urllib.request.urlretrieve(url, filepath)
        return filepath
    except Exception as e:
        print(f"Error downloading music: {e}")
        return None


def get_free_music(genre: str = "horror") -> Optional[str]:
    """Get a free background music file by genre."""
    if genre not in FREE_MUSIC:
        genre = "horror"

    tracks = FREE_MUSIC[genre]
    track = random.choice(tracks)

    # Create filename from name hash
    filename = f"{track['name']}.mp3"

    return _download_music(track["url"], filename)


def choose_random_song() -> Optional[str]:
    """Choose a random audio file from Songs/ or download free music.

    First checks local Songs/ directory, then falls back to free music.
    """
    # Try local songs first
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

    # Fallback to free music
    return get_free_music("horror")


def list_genres() -> list:
    """List available music genres."""
    return list(FREE_MUSIC.keys())


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
    print("Available genres:", list_genres())
    print("Local songs:", get_local_songs())
