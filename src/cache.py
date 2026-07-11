"""Thread-safe JSON cache for account and video data."""

import os
import json
import threading

from typing import Any
from uuid import uuid4

from src.config import MP_DIR

_lock = threading.Lock()


def _cache_path(name: str) -> str:
    return os.path.join(MP_DIR, f"{name}.json")


def _read(name: str) -> dict[str, Any]:
    path = _cache_path(name)
    if not os.path.exists(path):
        return {"accounts": []}
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data if isinstance(data, dict) else {"accounts": []}


def _write(name: str, data: dict[str, Any]) -> None:
    path = _cache_path(name)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


def get_accounts(provider: str = "youtube") -> list[dict]:
    """Get all accounts for a provider (youtube)."""
    with _lock:
        return _read(provider).get("accounts", [])


def add_account(provider: str, account: dict) -> None:
    """Add an account to the cache."""
    with _lock:
        data = _read(provider)
        data.setdefault("accounts", []).append(account)
        _write(provider, data)


def remove_account(provider: str, account_id: str) -> bool:
    """Remove an account by ID. Returns True if found and removed."""
    with _lock:
        data = _read(provider)
        accounts = data.get("accounts", [])
        new_accounts = [a for a in accounts if a.get("id") != account_id]
        if len(new_accounts) == len(accounts):
            return False
        data["accounts"] = new_accounts
        _write(provider, data)
        return True


def add_video(account_id: str, video: dict) -> None:
    """Add a video record to a YouTube account."""
    with _lock:
        data = _read("youtube")
        for account in data.get("accounts", []):
            if account.get("id") == account_id:
                account.setdefault("videos", []).append(video)
                break
        _write("youtube", data)


def get_videos(account_id: str) -> list[dict]:
    """Get all videos for a YouTube account."""
    with _lock:
        data = _read("youtube")
        for account in data.get("accounts", []):
            if account.get("id") == account_id:
                return account.get("videos", [])
        return []


def generate_uuid() -> str:
    return str(uuid4())
