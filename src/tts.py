"""Microsoft Edge TTS wrapper (free, high-quality, multi-language)."""

import os
import asyncio

from src.config import MP_DIR, get_tts_voice, get
from src.status import info

EDGE_SAMPLE_RATE = 24000


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
