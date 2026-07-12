"""Multi-channel batch generation."""

import os
import sys
import time
import threading
from datetime import datetime

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from src.config import reload_config, get as cfg_get
from src.llm import select_model, get_active_model
from src.cache import get_accounts
from src.tts import TTS
from src.youtube import YouTube
from src.status import info, success, warning, error


def generate_video_for_account(account: dict, config_overrides: dict = None) -> dict:
    """Generate a video for a specific account.
    
    Returns:
        dict with success, video_path, error, etc.
    """
    try:
        info(f"=== Generating video for: {account['nickname']} ({account['niche']}) ===")
        
        # Reload config with overrides
        from src import config
        config._config_cache = None
        reload_config()
        
        if config_overrides:
            for key, value in config_overrides.items():
                config._config_cache[key] = value
        
        # Select model
        model = get_active_model() or cfg_get("ollama_model", "")
        if model:
            select_model(model)
        
        # Generate video
        tts = TTS()
        yt = YouTube(
            account_uuid=account["id"],
            account_nickname=account["nickname"],
            fp_profile_path=account["firefox_profile"],
            niche=account["niche"],
            language=account["language"],
        )
        
        try:
            yt.generate_video(tts)
            result = {
                "success": True,
                "account": account["nickname"],
                "video_path": yt.video_path,
                "metadata": yt.metadata,
                "topic": yt.subject,
                "thumbnail": getattr(yt, "thumbnail_path", None),
            }
            success(f"Video generated for {account['nickname']}: {yt.video_path}")
            return result
        finally:
            yt.close()
            
    except Exception as e:
        error(f"Failed to generate video for {account['nickname']}: {e}")
        return {
            "success": False,
            "account": account["nickname"],
            "error": str(e),
        }


def generate_batch(accounts: list = None, videos_per_account: int = 1, config_overrides: dict = None) -> list:
    """Generate videos for multiple accounts.
    
    Args:
        accounts: List of accounts. If None, uses all YouTube accounts.
        videos_per_account: Number of videos to generate per account.
        config_overrides: Config overrides to apply.
    
    Returns:
        List of results for each video generated.
    """
    if accounts is None:
        accounts = get_accounts("youtube")
    
    if not accounts:
        error("No accounts found.")
        return []
    
    info(f"Starting batch generation: {len(accounts)} accounts, {videos_per_account} videos each")
    
    results = []
    
    for account in accounts:
        for i in range(videos_per_account):
            info(f"\n--- Video {i+1}/{videos_per_account} for {account['nickname']} ---")
            result = generate_video_for_account(account, config_overrides)
            results.append(result)
            
            # Delay between videos to avoid rate limits
            if i < videos_per_account - 1:
                info("Waiting 30 seconds before next video...")
                time.sleep(30)
    
    # Summary
    successful = len([r for r in results if r["success"]])
    failed = len([r for r in results if not r["success"]])
    
    info(f"\n=== Batch complete: {successful} successful, {failed} failed ===")
    
    return results


class BatchWorker(threading.Thread):
    """Background thread for batch generation."""
    
    def __init__(self, accounts: list, videos_per_account: int, config_overrides: dict = None):
        super().__init__(daemon=True)
        self.accounts = accounts
        self.videos_per_account = videos_per_account
        self.config_overrides = config_overrides or {}
        self.results = []
        self._progress = {"current": 0, "total": 0, "status": "idle"}
    
    def run(self):
        self._progress["status"] = "running"
        self._progress["total"] = len(self.accounts) * self.videos_per_account
        
        try:
            self.results = generate_batch(
                self.accounts,
                self.videos_per_account,
                self.config_overrides,
            )
            self._progress["status"] = "done"
        except Exception as e:
            error(f"Batch worker error: {e}")
            self._progress["status"] = "error"
            self._progress["error"] = str(e)
    
    def get_progress(self) -> dict:
        return self._progress.copy()


if __name__ == "__main__":
    print("Multi-Channel Batch Generator")
    accounts = get_accounts("youtube")
    print(f"Found {len(accounts)} accounts:")
    for acc in accounts:
        print(f"  - {acc['nickname']} ({acc['niche']})")
