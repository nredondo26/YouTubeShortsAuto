"""Singleton configuration loader. Reads config.json once and caches it."""

import os
import sys
import json
from typing import Any

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_PATH = os.path.join(ROOT_DIR, "config.json")
MP_DIR = os.path.join(ROOT_DIR, ".mp")
FONTS_DIR = os.path.join(ROOT_DIR, "fonts")
SONGS_DIR = os.path.join(ROOT_DIR, "Songs")

_config_cache: dict[str, Any] | None = None


def _load_config() -> dict[str, Any]:
    global _config_cache
    if _config_cache is None:
        if not os.path.exists(CONFIG_PATH):
            raise FileNotFoundError(
                f"config.json not found at {CONFIG_PATH}. "
                "Copy config.example.json to config.json and fill in your settings."
            )
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            _config_cache = json.load(f)
    return _config_cache


def reload_config() -> dict[str, Any]:
    """Force reload config from disk."""
    global _config_cache
    _config_cache = None
    return _load_config()


def get(key: str, default: Any = None) -> Any:
    return _load_config().get(key, default)


def get_required(key: str) -> Any:
    value = get(key)
    if value is None or value == "":
        raise ValueError(f"Required config key '{key}' is missing or empty.")
    return value


def ensure_directories() -> None:
    os.makedirs(MP_DIR, exist_ok=True)


def get_first_time() -> bool:
    return not os.path.exists(MP_DIR)


def get_verbose() -> bool:
    return bool(get("verbose", False))


def get_headless() -> bool:
    return bool(get("headless", False))


def get_threads() -> int:
    return int(get("threads", 2))


def get_is_for_kids() -> bool:
    return bool(get("is_for_kids", False))


def get_firefox_profile_path() -> str:
    return str(get_required("firefox_profile"))


def get_ollama_base_url() -> str:
    return str(get("ollama_base_url", "http://127.0.0.1:11434"))


def get_ollama_model() -> str:
    return str(get("ollama_model", ""))


def get_nanobanana2_api_base_url() -> str:
    return str(get("nanobanana2_api_base_url", "https://generativelanguage.googleapis.com/v1beta"))


def get_nanobanana2_api_key() -> str:
    configured = str(get("nanobanana2_api_key", ""))
    if configured:
        return configured
    return os.environ.get("GEMINI_API_KEY", "")


def get_nanobanana2_model() -> str:
    return str(get("nanobanana2_model", "gemini-3.1-flash-image-preview"))


def get_nanobanana2_aspect_ratio() -> str:
    return str(get("nanobanana2_aspect_ratio", "9:16"))


def get_tts_voice() -> str:
    return str(get("tts_voice", "Jasper"))


def get_stt_provider() -> str:
    return str(get("stt_provider", "local_whisper"))


def get_whisper_model() -> str:
    return str(get("whisper_model", "base"))


def get_whisper_device() -> str:
    return str(get("whisper_device", "auto"))


def get_whisper_compute_type() -> str:
    return str(get("whisper_compute_type", "int8"))


def get_assemblyai_api_key() -> str:
    return str(get("assembly_ai_api_key", ""))


def get_font() -> str:
    return str(get("font", "bold_font.ttf"))


def get_fonts_dir() -> str:
    return FONTS_DIR


def get_imagemagick_path() -> str:
    return str(get_required("imagemagick_path"))


def get_script_sentence_length() -> int:
    return int(get("script_sentence_length", 4))


def get_subtitle_max_chars() -> int:
    return int(get("subtitle_max_chars", 40))


def get_subtitle_color() -> str:
    return str(get("subtitle_color", "#FFFF00"))


def get_subtitle_stroke_color() -> str:
    return str(get("subtitle_stroke_color", "#000000"))


def get_subtitle_stroke_width() -> int:
    return int(get("subtitle_stroke_width", 4))


def get_subtitle_font_size() -> int:
    return int(get("subtitle_font_size", 80))


def get_subtitle_position() -> str:
    return str(get("subtitle_position", "center"))


def get_subtitle_max_width() -> int:
    return int(get("subtitle_max_width", 1000))


def get_zip_url() -> str:
    return str(get("zip_url", ""))


def get_max_script_retries() -> int:
    return int(get("max_script_retries", 3))


def get_max_metadata_retries() -> int:
    return int(get("max_metadata_retries", 3))


def get_max_prompts_retries() -> int:
    return int(get("max_prompts_retries", 3))


def validate_youtube_config() -> list[str]:
    """Validate that all required YouTube settings are present. Returns list of errors."""
    errors = []
    try:
        get_firefox_profile_path()
    except ValueError:
        errors.append("firefox_profile is not configured")

    if not get_nanobanana2_api_key():
        errors.append("nanobanana2_api_key is not configured (or GEMINI_API_KEY env var)")

    try:
        get_imagemagick_path()
    except ValueError:
        errors.append("imagemagick_path is not configured")

    if not os.path.isdir(FONTS_DIR):
        errors.append(f"fonts directory not found at {FONTS_DIR}")

    return errors
