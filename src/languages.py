"""Multi-language support for YouTubeShortsAuto."""

import os
import sys
from typing import Dict, List, Optional

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)


# Supported languages with their configurations
SUPPORTED_LANGUAGES = {
    "es": {
        "name": "Español",
        "native_name": "Español",
        "tts_voice": "es-CO-GonzaloNeural",
        "tts_rate": "-10%",
        "whisper_language": "es",
        "default_prompt_topic": "horror story",
        "subtitle_chars": 40,
        "timezone": "America/Bogota",
    },
    "en": {
        "name": "English",
        "native_name": "English",
        "tts_voice": "en-US-GuyNeural",
        "tts_rate": "-5%",
        "whisper_language": "en",
        "default_prompt_topic": "scary story",
        "subtitle_chars": 45,
        "timezone": "America/New_York",
    },
    "pt": {
        "name": "Português",
        "native_name": "Português",
        "tts_voice": "pt-BR-AntonioNeural",
        "tts_rate": "-10%",
        "whisper_language": "pt",
        "default_prompt_topic": "história de terror",
        "subtitle_chars": 42,
        "timezone": "America/Sao_Paulo",
    },
    "fr": {
        "name": "Français",
        "native_name": "Français",
        "tts_voice": "fr-FR-HenriNeural",
        "tts_rate": "-5%",
        "whisper_language": "fr",
        "default_prompt_topic": "histoire d'horreur",
        "subtitle_chars": 42,
        "timezone": "Europe/Paris",
    },
    "de": {
        "name": "Deutsch",
        "native_name": "Deutsch",
        "tts_voice": "de-DE-ConradNeural",
        "tts_rate": "-5%",
        "whisper_language": "de",
        "default_prompt_topic": "Schreckgeschichte",
        "subtitle_chars": 45,
        "timezone": "Europe/Berlin",
    },
    "it": {
        "name": "Italiano",
        "native_name": "Italiano",
        "tts_voice": "it-IT-DiegoNeural",
        "tts_rate": "-5%",
        "whisper_language": "it",
        "default_prompt_topic": "storia dell'orrore",
        "subtitle_chars": 42,
        "timezone": "Europe/Rome",
    },
    "ja": {
        "name": "日本語",
        "native_name": "日本語",
        "tts_voice": "ja-JP-KeitaNeural",
        "tts_rate": "-10%",
        "whisper_language": "ja",
        "default_prompt_topic": "ホラー",
        "subtitle_chars": 30,
        "timezone": "Asia/Tokyo",
    },
    "ko": {
        "name": "한국어",
        "native_name": "한국어",
        "tts_voice": "ko-KR-InJoonNeural",
        "tts_rate": "-10%",
        "whisper_language": "ko",
        "default_prompt_topic": "공포 이야기",
        "subtitle_chars": 30,
        "timezone": "Asia/Seoul",
    },
    "zh": {
        "name": "中文",
        "native_name": "中文",
        "tts_voice": "zh-CN-YunxiNeural",
        "tts_rate": "-10%",
        "whisper_language": "zh",
        "default_prompt_topic": "恐怖故事",
        "subtitle_chars": 25,
        "timezone": "Asia/Shanghai",
    },
    "hi": {
        "name": "हिन्दी",
        "native_name": "हिन्दी",
        "tts_voice": "hi-IN-MadhurNeural",
        "tts_rate": "-10%",
        "whisper_language": "hi",
        "default_prompt_topic": "डरावनी कहानी",
        "subtitle_chars": 35,
        "timezone": "Asia/Kolkata",
    },
}


def get_supported_languages() -> List[str]:
    """Get list of supported language codes."""
    return list(SUPPORTED_LANGUAGES.keys())


def get_language_config(language_code: str) -> Optional[Dict]:
    """Get configuration for a specific language."""
    return SUPPORTED_LANGUAGES.get(language_code)


def get_language_name(language_code: str, native: bool = False) -> str:
    """Get display name for a language."""
    config = get_language_config(language_code)
    if config:
        return config["native_name"] if native else config["name"]
    return language_code


def get_tts_voice(language_code: str) -> str:
    """Get TTS voice for a language."""
    config = get_language_config(language_code)
    if config:
        return config["tts_voice"]
    return "en-US-GuyNeural"  # Default


def get_tts_rate(language_code: str) -> str:
    """Get TTS rate for a language."""
    config = get_language_config(language_code)
    if config:
        return config["tts_rate"]
    return "0%"


def get_whisper_language(language_code: str) -> str:
    """Get Whisper language code."""
    config = get_language_config(language_code)
    if config:
        return config["whisper_language"]
    return "en"


def get_prompt_topic(language_code: str) -> str:
    """Get default prompt topic for a language."""
    config = get_language_config(language_code)
    if config:
        return config["default_prompt_topic"]
    return "scary story"


def get_subtitle_chars(language_code: str) -> int:
    """Get recommended subtitle characters per line for a language."""
    config = get_language_config(language_code)
    if config:
        return config["subtitle_chars"]
    return 40


def format_language_list() -> List[str]:
    """Format language list for display."""
    result = []
    for code, config in SUPPORTED_LANGUAGES.items():
        result.append(f"{code} - {config['name']} ({config['native_name']})")
    return result


if __name__ == "__main__":
    print("Supported languages:")
    for code, config in SUPPORTED_LANGUAGES.items():
        print(f"  {code}: {config['name']} ({config['native_name']})")
        print(f"    Voice: {config['tts_voice']}")
        print(f"    Rate: {config['tts_rate']}")
        print()
