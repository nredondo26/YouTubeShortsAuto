"""Microsoft Edge TTS wrapper (free, high-quality, multi-language)."""

import os
import asyncio

from src.config import MP_DIR, get_tts_voice, get
from src.status import info

EDGE_SAMPLE_RATE = 24000

SAMPLE_TEXTS = {
    "es": "Esta es una prueba de voz para tu canal de YouTube Shorts. Las historias de terror son fascinantes.",
    "en": "This is a voice test for your YouTube Shorts channel. Horror stories are fascinating.",
    "pt": "Este e um teste de voz para seu canal do YouTube Shorts. Historias de terror sao fascinantes.",
    "fr": "Ceci est un test vocal pour votre chaîne YouTube Shorts. Les histoires d'horreur sont fascinantes.",
    "de": "Dies ist ein Sprachtest für deinen YouTube Shorts Kanal. Gruselgeschichten sind faszinierend.",
    "it": "Questo e un test vocale per il tuo canale YouTube Shorts. Le storie dell'orrore sono affascinanti.",
    "ja": "これはYouTubeショーツチャンネルの声のテストです。ホラーの物語は魅力的です。",
    "ko": "이것은 YouTube 채널을위한 음성 테스트입니다. 공포 이야기는 매력적입니다.",
    "zh": "这是YouTube Shorts频道的声音测试。恐怖故事非常迷人。",
    "hi": "यह आपके YouTube Shorts चैनल के लिए एक आवाज़ परीक्षण है। डरावनी कहानियाँ आकर्षक होती हैं।",
}


class TTS:
    def __init__(self) -> None:
        self._voice = get_tts_voice()
        self._rate = get("tts_rate", "+0%")

    def synthesize(self, text: str, output_path: str | None = None) -> str:
        """Convert text to speech using Microsoft Edge TTS.

        Args:
            text: The text to synthesize.
            output_path: Optional output path. Defaults to .mp/tts_<uuid>.mp3

        Returns:
            Path to the generated audio file.
        """
        if output_path is None:
            from uuid import uuid4
            output_path = os.path.join(MP_DIR, f"tts_{uuid4()}.mp3")

        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        asyncio.run(self._generate(text, output_path))

        if not os.path.exists(output_path) or os.path.getsize(output_path) == 0:
            raise RuntimeError(f"TTS produced empty file: {output_path}")

        info(f"TTS audio saved (rate={self._rate}): {output_path}")
        return output_path

    async def _generate(self, text: str, output_path: str) -> None:
        import edge_tts

        communicate = edge_tts.Communicate(text, self._voice, rate=self._rate)
        await communicate.save(output_path)


def list_voices(language: str = "es") -> list[dict]:
    """List available Edge TTS voices for a language code (e.g. 'es', 'en')."""
    import edge_tts

    async def _get():
        voices = await edge_tts.list_voices()
        return [v for v in voices if v["Locale"].startswith(language)]

    return asyncio.run(_get())


def generate_voice_sample(voice_id: str, language: str = "es", rate: str = "+0%") -> str | None:
    """Generate a sample audio file for a voice.
    
    Args:
        voice_id: The voice ID (e.g. 'es-CO-GonzaloNeural')
        language: Language code for sample text
        rate: Speech rate (e.g. '+0%', '-10%')
    
    Returns:
        Path to the generated sample audio file, or None on error
    """
    import edge_tts
    from uuid import uuid4
    
    sample_text = SAMPLE_TEXTS.get(language, SAMPLE_TEXTS["es"])
    output_path = os.path.join(MP_DIR, f"voice_sample_{uuid4()}.mp3")
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    async def _generate():
        communicate = edge_tts.Communicate(sample_text, voice_id, rate=rate)
        await communicate.save(output_path)
    
    try:
        asyncio.run(_generate())
        if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
            return output_path
    except Exception as e:
        print(f"Error generating voice sample: {e}")
    
    return None


def get_all_voices() -> list[dict]:
    """Get all available Edge TTS voices."""
    import edge_tts
    
    async def _get():
        return await edge_tts.list_voices()
    
    return asyncio.run(_get())
