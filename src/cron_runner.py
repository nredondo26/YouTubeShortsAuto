"""CRON runner for scheduled YouTube Shorts uploads.

Usage: python src/cron_runner.py <account_id> [model_name]
"""

import sys
import os

# Ensure project root is on sys.path
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from src.config import ensure_directories, get_verbose
from src.llm import select_model
from src.cache import get_accounts
from src.tts import TTS
from src.youtube import YouTube
from src.utils import rem_temp_files
from src.status import info, success, warning, error


def main():
    if len(sys.argv) < 2:
        error("Usage: python src/cron_runner.py <account_id> [model_name]")
        sys.exit(1)

    account_id = sys.argv[1]
    model = sys.argv[2] if len(sys.argv) > 2 else None

    if not model:
        error("No Ollama model specified as second argument.")
        sys.exit(1)

    select_model(model)
    ensure_directories()
    rem_temp_files()

    accounts = get_accounts("youtube")
    target = None
    for acc in accounts:
        if acc.get("id") == account_id:
            target = acc
            break

    if not target:
        error(f"Account {account_id} not found.")
        sys.exit(1)

    yt = None
    try:
        info(f"Running scheduled upload for: {target['nickname']}")
        tts = TTS()
        yt = YouTube(
            account_id=target["id"],
            account_nickname=target["nickname"],
            fp_profile_path=target["firefox_profile"],
            niche=target["niche"],
            language=target["language"],
        )
        yt.generate_video(tts)
        upload_ok = yt.upload_video()
        if upload_ok:
            success(f"Scheduled upload complete: {yt.uploaded_video_url}")
        else:
            warning("Scheduled upload failed.")
    except Exception as e:
        error(f"Scheduled job failed: {e}")
    finally:
        if yt:
            yt.close()


if __name__ == "__main__":
    main()
