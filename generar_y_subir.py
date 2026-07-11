"""Genera un video y lo sube a YouTube. Uso: py generar_y_subir.py"""

import sys
import os

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from src.config import reload_config, get_ollama_model
from src.llm import select_model, get_active_model
from src.cache import get_accounts
from src.tts import TTS
from src.youtube import YouTube


def main():
    accounts = get_accounts("youtube")
    if not accounts:
        print("No hay cuentas configuradas. Ejecuta la web UI primero para crear una.")
        return

    acc = accounts[0]
    print(f"Cuenta: {acc['nickname']} ({acc['niche']})")

    reload_config()
    model = get_active_model() or get_ollama_model()
    if model:
        select_model(model)
        print(f"Modelo: {model}")

    tts = TTS()
    yt = YouTube(
        account_uuid=acc["id"],
        account_nickname=acc["nickname"],
        fp_profile_path=acc["firefox_profile"],
        niche=acc["niche"],
        language=acc["language"],
    )

    try:
        print("\n--- Generando video ---")
        yt.generate_video(tts)
        print(f"\nVideo listo: {yt.video_path}")

        print("\n--- Subiendo a YouTube ---")
        yt.upload_video()
        print(f"\nSubido: {yt.uploaded_video_url}")
    except Exception as e:
        print(f"\nError: {e}")
    finally:
        yt.close()


if __name__ == "__main__":
    main()
