"""Upload scheduler - programar uploads a horas pico."""

import os
import sys
import time
import json
import threading
from datetime import datetime, timedelta
from typing import Optional

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from src.config import MP_DIR, get as cfg_get
from src.cache import get_accounts, get_videos
from src.status import info, success, warning, error

SCHEDULE_FILE = os.path.join(ROOT_DIR, "schedule.json")


def _load_schedule() -> dict:
    if os.path.exists(SCHEDULE_FILE):
        with open(SCHEDULE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"scheduled_uploads": [], "settings": {"enabled": False, "upload_hours": [18, 19, 20, 21]}}


def _save_schedule(data: dict):
    with open(SCHEDULE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def schedule_upload(video_path: str, account_id: str, title: str, description: str, tags: list = None):
    """Schedule a video for upload at the next optimal time."""
    schedule = _load_schedule()
    
    upload_entry = {
        "video_path": video_path,
        "account_id": account_id,
        "title": title,
        "description": description,
        "tags": tags or [],
        "scheduled_time": None,
        "status": "pending",
        "created_at": datetime.now().isoformat(),
    }
    
    schedule["scheduled_uploads"].append(upload_entry)
    _save_schedule(schedule)
    info(f"Video scheduled for upload: {title[:50]}...")
    return len(schedule["scheduled_uploads"]) - 1


def get_next_upload_time() -> Optional[datetime]:
    """Get the next optimal upload time based on settings."""
    schedule = _load_schedule()
    settings = schedule.get("settings", {})
    upload_hours = settings.get("upload_hours", [18, 19, 20, 21])
    
    now = datetime.now()
    current_hour = now.hour
    
    # Find next upload hour
    for hour in sorted(upload_hours):
        if hour > current_hour:
            return now.replace(hour=hour, minute=0, second=0, microsecond=0)
    
    # If no more hours today, use first hour tomorrow
    tomorrow = now + timedelta(days=1)
    return tomorrow.replace(hour=upload_hours[0], minute=0, second=0, microsecond=0)


def process_pending_uploads():
    """Process all pending uploads at their scheduled times."""
    schedule = _load_schedule()
    settings = schedule.get("settings", {})
    
    if not settings.get("enabled", False):
        return
    
    upload_hours = settings.get("upload_hours", [18, 19, 20, 21])
    now = datetime.now()
    
    # Check if we're in an upload window
    if now.hour not in upload_hours:
        return
    
    pending = [u for u in schedule["scheduled_uploads"] if u["status"] == "pending"]
    
    for upload in pending:
        try:
            info(f"Processing scheduled upload: {upload['title'][:50]}...")
            
            # Find the account
            accounts = get_accounts("youtube")
            account = next((a for a in accounts if a["id"] == upload["account_id"]), None)
            
            if not account:
                warning(f"Account not found for upload: {upload['account_id']}")
                upload["status"] = "error"
                upload["error"] = "Account not found"
                continue
            
            # Import and run upload
            from src.youtube import YouTube
            from src.tts import TTS
            
            yt = YouTube(
                account_uuid=account["id"],
                account_nickname=account["nickname"],
                fp_profile_path=account["firefox_profile"],
                niche=account["niche"],
                language=account["language"],
            )
            
            try:
                yt.video_path = upload["video_path"]
                yt.metadata = {
                    "title": upload["title"],
                    "description": upload["description"],
                    "tags": upload.get("tags", []),
                }
                
                yt.upload_video()
                upload["status"] = "uploaded"
                upload["uploaded_at"] = datetime.now().isoformat()
                upload["url"] = yt.uploaded_video_url
                success(f"Uploaded: {upload['url']}")
            finally:
                yt.close()
                
        except Exception as e:
            error(f"Upload failed: {e}")
            upload["status"] = "error"
            upload["error"] = str(e)
    
    _save_schedule(schedule)


def get_schedule_status() -> dict:
    """Get current schedule status."""
    schedule = _load_schedule()
    pending = len([u for u in schedule["scheduled_uploads"] if u["status"] == "pending"])
    uploaded = len([u for u in schedule["scheduled_uploads"] if u["status"] == "uploaded"])
    errors = len([u for u in schedule["scheduled_uploads"] if u["status"] == "error"])
    next_time = get_next_upload_time()
    
    return {
        "enabled": schedule["settings"].get("enabled", False),
        "upload_hours": schedule["settings"].get("upload_hours", [18, 19, 20, 21]),
        "pending": pending,
        "uploaded": uploaded,
        "errors": errors,
        "next_upload": next_time.isoformat() if next_time else None,
    }


def update_schedule_settings(enabled: bool = None, upload_hours: list = None):
    """Update schedule settings."""
    schedule = _load_schedule()
    
    if enabled is not None:
        schedule["settings"]["enabled"] = enabled
    if upload_hours is not None:
        schedule["settings"]["upload_hours"] = upload_hours
    
    _save_schedule(schedule)
    info(f"Schedule settings updated: enabled={schedule['settings']['enabled']}, hours={schedule['settings']['upload_hours']}")


def cancel_scheduled_upload(index: int):
    """Cancel a scheduled upload by index."""
    schedule = _load_schedule()
    if 0 <= index < len(schedule["scheduled_uploads"]):
        upload = schedule["scheduled_uploads"][index]
        if upload["status"] == "pending":
            upload["status"] = "cancelled"
            _save_schedule(schedule)
            info(f"Cancelled upload: {upload['title'][:50]}...")
        else:
            warning(f"Cannot cancel upload with status: {upload['status']}")


def clear_completed_uploads():
    """Clear all completed or cancelled uploads."""
    schedule = _load_schedule()
    schedule["scheduled_uploads"] = [
        u for u in schedule["scheduled_uploads"]
        if u["status"] == "pending"
    ]
    _save_schedule(schedule)
    info("Cleared completed uploads from schedule")


class SchedulerDaemon(threading.Thread):
    """Background thread that processes scheduled uploads."""
    
    def __init__(self):
        super().__init__(daemon=True)
        self._stop_event = threading.Event()
    
    def run(self):
        info("Scheduler daemon started")
        while not self._stop_event.is_set():
            try:
                process_pending_uploads()
            except Exception as e:
                error(f"Scheduler error: {e}")
            
            # Check every 5 minutes
            self._stop_event.wait(300)
    
    def stop(self):
        self._stop_event.set()


_scheduler_daemon = None

def start_scheduler():
    """Start the scheduler daemon."""
    global _scheduler_daemon
    if _scheduler_daemon is None or not _scheduler_daemon.is_alive():
        _scheduler_daemon = SchedulerDaemon()
        _scheduler_daemon.start()
        success("Scheduler daemon started")


def stop_scheduler():
    """Stop the scheduler daemon."""
    global _scheduler_daemon
    if _scheduler_daemon and _scheduler_daemon.is_alive():
        _scheduler_daemon.stop()
        _scheduler_daemon.join(timeout=5)
        _scheduler_daemon = None
        info("Scheduler daemon stopped")


if __name__ == "__main__":
    print("Schedule Status:")
    status = get_schedule_status()
    for key, value in status.items():
        print(f"  {key}: {value}")
