"""Ambient sound effects for horror videos."""

import os
import sys
import random
import hashlib
from typing import Optional

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

SFX_DIR = os.path.join(ROOT_DIR, ".mp", "sfx")
os.makedirs(SFX_DIR, exist_ok=True)

# Free ambient sound URLs (freesound.org compatible)
AMBIENT_SOUNDS = {
    "rain": [
        "https://cdn.freesound.org/previews/531/531947_6244298-lq.mp3",
        "https://cdn.freesound.org/previews/527/527327_11861866-lq.mp3",
    ],
    "wind": [
        "https://cdn.freesound.org/previews/467/467452_9497060-lq.mp3",
        "https://cdn.freesound.org/previews/177/177489_1015240-lq.mp3",
    ],
    "thunder": [
        "https://cdn.freesound.org/previews/415/415481_2903256-lq.mp3",
        "https://cdn.freesound.org/previews/166/166861_1015240-lq.mp3",
    ],
    "creepy": [
        "https://cdn.freesound.org/previews/521/521733_11861866-lq.mp3",
        "https://cdn.freesound.org/previews/371/371368_5440187-lq.mp3",
    ],
    "heartbeat": [
        "https://cdn.freesound.org/previews/331/331776_2398403-lq.mp3",
    ],
    "whispers": [
        "https://cdn.freesound.org/previews/458/458822_9497060-lq.mp3",
    ],
}

# Horror-specific sound combinations
HORROR_PRESETS = {
    "lluvia_siniestra": ["rain", "wind", "creepy"],
    "tormenta": ["rain", "thunder", "wind"],
    "bosque_oscuro": ["wind", "creepy", "whispers"],
    "casa_encantada": ["creepy", "whispers", "heartbeat"],
    "noche_de_truenos": ["thunder", "rain", "wind"],
    "suspense": ["heartbeat", "creepy"],
}


def _download_sound(url: str, filename: str) -> Optional[str]:
    """Download a sound file if not already cached."""
    filepath = os.path.join(SFX_DIR, filename)

    if os.path.exists(filepath):
        return filepath

    try:
        import urllib.request
        urllib.request.urlretrieve(url, filepath)
        return filepath
    except Exception as e:
        print(f"Error downloading sound: {e}")
        return None


def get_ambient_sound(sound_type: str) -> Optional[str]:
    """Get an ambient sound file by type."""
    if sound_type not in AMBIENT_SOUNDS:
        return None

    urls = AMBIENT_SOUNDS[sound_type]
    url = random.choice(urls)

    # Create filename from URL hash
    url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
    filename = f"{sound_type}_{url_hash}.mp3"

    return _download_sound(url, filename)


def get_horror_preset(preset_name: str) -> list:
    """Get list of sound files for a horror preset."""
    if preset_name not in HORROR_PRESETS:
        return []

    sound_types = HORROR_PRESETS[preset_name]
    sounds = []

    for sound_type in sound_types:
        sound_path = get_ambient_sound(sound_type)
        if sound_path:
            sounds.append(sound_path)

    return sounds


def list_presets() -> list:
    """List all available horror presets."""
    return list(HORROR_PRESETS.keys())


def list_sounds() -> list:
    """List all available ambient sound types."""
    return list(AMBIENT_SOUNDS.keys())


def add_ambient_to_video(video_path: str, preset: str = "lluvia_siniestra", volume: float = 0.15) -> str:
    """Add ambient sounds to a video.

    Args:
        video_path: Path to the video file
        preset: Horror preset name
        volume: Volume level (0.0 to 1.0)

    Returns:
        Path to the new video with ambient sounds
    """
    from moviepy import VideoFileClip, AudioFileClip, CompositeAudioClip

    sounds = get_horror_preset(preset)
    if not sounds:
        print(f"No sounds available for preset: {preset}")
        return video_path

    try:
        video = VideoFileClip(video_path)
        audio_clips = []

        # Add original audio if exists
        if video.audio:
            audio_clips.append(video.audio)

        # Add ambient sounds
        for sound_path in sounds:
            try:
                ambient = AudioFileClip(sound_path)
                # Loop or trim to match video duration
                if ambient.duration < video.duration:
                    # Loop the sound
                    loops_needed = int(video.duration / ambient.duration) + 1
                    from moviepy import concatenate_audioclips
                    ambient = concatenate_audioclips([ambient] * loops_needed)
                ambient = subclip(ambient, 0, video.duration)
                ambient = multiply_volume(ambient, volume)
                audio_clips.append(ambient)
            except Exception as e:
                print(f"Error loading ambient sound: {e}")

        if len(audio_clips) > 1:
            # Mix all audio tracks
            final_audio = CompositeAudioClip(audio_clips)
            video = video.with_audio(final_audio)

        # Save to new file
        base, ext = os.path.splitext(video_path)
        output_path = f"{base}_ambient{ext}"

        video.write_videofile(
            output_path,
            codec="libx264",
            audio_codec="aac",
            logger=None,
        )

        video.close()
        return output_path

    except Exception as e:
        print(f"Error adding ambient sounds: {e}")
        return video_path


if __name__ == "__main__":
    print("Available presets:")
    for preset in list_presets():
        print(f"  - {preset}")

    print("\nAvailable sounds:")
    for sound in list_sounds():
        print(f"  - {sound}")
