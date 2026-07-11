"""YouTubeShortsAuto - YouTube Shorts Automation CLI.

Entry point with signal handling, proper error management,
and a clean interactive menu (no recursive main calls).
"""

import os
import sys
import signal
import subprocess

from prettytable import PrettyTable

from src.config import (
    ROOT_DIR,
    ensure_directories,
    get_first_time,
    get_verbose,
    get_ollama_model,
    get_firefox_profile_path,
)
from src.llm import list_models, select_model, get_active_model
from src.cache import get_accounts, add_account, remove_account, generate_uuid
from src.utils import rem_temp_files, fetch_songs, close_selenium_instances
from src.tts import TTS
from src.youtube import YouTube
from src.status import info, success, warning, error, header, ask


def _signal_handler(sig, frame):
    print()
    info("Shutting down...")
    close_selenium_instances()
    sys.exit(0)


def _print_banner():
    banner_path = os.path.join(ROOT_DIR, "assets", "banner.txt")
    if os.path.exists(banner_path):
        with open(banner_path, "r", encoding="utf-8") as f:
            print(f.read())
    else:
        print("""
========================================
       YouTubeShortsAuto v1.0
   YouTube Shorts Automation CLI
========================================
""")


def _select_ollama_model():
    """Select the Ollama model (from config or interactively)."""
    configured = get_ollama_model()
    if configured:
        select_model(configured)
        success(f"Using configured model: {configured}")
        return

    try:
        models = list_models()
    except Exception as e:
        error(f"Cannot connect to Ollama at configured URL: {e}")
        sys.exit(1)

    if not models:
        error("No models found on Ollama. Pull one first: ollama pull llama3.2:3b")
        sys.exit(1)

    header("OLLAMA MODELS")
    for idx, name in enumerate(models, 1):
        print(f"  {idx}. {name}")

    while True:
        raw = ask("Select a model number")
        try:
            choice = int(raw) - 1
            if 0 <= choice < len(models):
                select_model(models[choice])
                success(f"Using model: {models[choice]}")
                return
        except ValueError:
            pass
        warning("Invalid selection. Try again.")


def _manage_account_interactive() -> dict | None:
    """Interactive account selection/creation for YouTube. Returns selected account or None."""
    accounts = get_accounts("youtube")

    if not accounts:
        warning("No YouTube accounts found.")
        create = ask("Create one now? (yes/no)")
        if create.lower() not in ("y", "yes"):
            return None

        uuid = generate_uuid()
        info(f"Generated UUID: {uuid}")
        nickname = ask("Nickname for this account")
        fp_path = ask("Path to Firefox profile directory")
        niche = ask("Channel niche (e.g. 'tech facts')")
        language = ask("Language (e.g. 'English', 'Spanish')")

        account = {
            "id": uuid,
            "nickname": nickname,
            "firefox_profile": fp_path,
            "niche": niche,
            "language": language,
            "videos": [],
        }
        add_account("youtube", account)
        success("Account created!")
        return account

    # Show existing accounts
    header("YOUR ACCOUNTS")
    table = PrettyTable()
    table.field_names = ["#", "UUID", "Nickname", "Niche"]
    for idx, acc in enumerate(accounts, 1):
        table.add_row([idx, acc["id"][:8] + "...", acc["nickname"], acc["niche"]])
    print(table)

    raw = ask("Select account number ('d' to delete, 'c' to create new)")
    if raw.lower() == "d":
        del_num = ask("Enter account number to delete")
        try:
            idx = int(del_num) - 1
            if 0 <= idx < len(accounts):
                confirm = ask(f"Delete '{accounts[idx]['nickname']}'? (yes/no)")
                if confirm.lower() in ("y", "yes"):
                    remove_account("youtube", accounts[idx]["id"])
                    success("Account deleted.")
            else:
                error("Invalid account number.")
        except ValueError:
            error("Invalid input.")
        return None

    if raw.lower() == "c":
        return _manage_account_interactive()

    try:
        idx = int(raw) - 1
        if 0 <= idx < len(accounts):
            return accounts[idx]
    except ValueError:
        pass

    error("Invalid selection.")
    return None


def _youtube_menu(account: dict):
    """Run the YouTube Shorts submenu for a selected account."""
    tts = TTS()

    while True:
        rem_temp_files()
        header(f"YOUTUBE SHORTS - {account['nickname']}")
        for idx, option in enumerate(["Upload Short", "Show all Shorts", "Setup CRON Job", "Quit"], 1):
            print(f"  {idx}. {option}")

        raw = ask("Select an option")
        try:
            choice = int(raw)
        except ValueError:
            error("Invalid input.")
            continue

        if choice == 1:
            _handle_upload_short(account, tts)
        elif choice == 2:
            _handle_show_shorts(account)
        elif choice == 3:
            _handle_cron_setup(account)
        elif choice == 4:
            break
        else:
            error("Invalid option.")


def _handle_upload_short(account: dict, tts: TTS):
    """Generate and optionally upload a YouTube Short."""
    yt = None
    try:
        yt = YouTube(
            account_uuid=account["id"],
            account_nickname=account["nickname"],
            fp_profile_path=account["firefox_profile"],
            niche=account["niche"],
            language=account["language"],
        )
        yt.generate_video(tts)

        upload = ask("Upload this video to YouTube? (yes/no)")
        if upload.lower() in ("y", "yes"):
            success = yt.upload_video()
            if not success:
                warning("Upload failed.")
    except Exception as e:
        error(f"Pipeline failed: {e}")
    finally:
        if yt:
            yt.close()


def _handle_show_shorts(account: dict):
    """Display previously uploaded shorts."""
    videos = get_accounts("youtube")  # re-read to get fresh data
    account_videos = []
    for acc in videos:
        if acc.get("id") == account["id"]:
            account_videos = acc.get("videos", [])
            break

    if not account_videos:
        warning("No videos found.")
        return

    header("UPLOADED SHORTS")
    table = PrettyTable()
    table.field_names = ["#", "Date", "Title"]
    for idx, v in enumerate(account_videos, 1):
        title = v.get("title", "Untitled")[:50]
        table.add_row([idx, v.get("date", "?"), title + "..."])
    print(table)


def _handle_cron_setup(account: dict):
    """Setup a CRON job for automatic uploads."""
    header("CRON SCHEDULE")
    options = ["Once a day", "Twice a day", "Thrice a day", "Quit"]
    for idx, opt in enumerate(options, 1):
        print(f"  {idx}. {opt}")

    raw = ask("Select frequency")
    try:
        choice = int(raw)
    except ValueError:
        return

    if choice == 4:
        return

    model = get_active_model()
    cron_script = os.path.join(ROOT_DIR, "src", "cron_runner.py")
    command = ["python", cron_script, account["id"], model or ""]

    import schedule as sched

    def job():
        subprocess.run(command)

    if choice == 1:
        sched.every(1).day.do(job)
        success("CRON: Once a day.")
    elif choice == 2:
        sched.every().day.at("10:00").do(job)
        sched.every().day.at("16:00").do(job)
        success("CRON: Twice a day.")
    elif choice == 3:
        sched.every().day.at("08:00").do(job)
        sched.every().day.at("14:00").do(job)
        sched.every().day.at("20:00").do(job)
        success("CRON: Thrice a day.")

    info("CRON jobs active. Press Ctrl+C to stop.")
    try:
        import time
        while True:
            sched.run_pending()
            time.sleep(60)
    except KeyboardInterrupt:
        info("CRON scheduler stopped.")


def main():
    """Main application loop."""
    signal.signal(signal.SIGINT, _signal_handler)
    signal.signal(signal.SIGTERM, _signal_handler)

    _print_banner()

    if get_first_time():
        info("First time running? Copy config.example.json to config.json and configure it.")

    ensure_directories()
    rem_temp_files()
    fetch_songs()
    _select_ollama_model()

    while True:
        header("MAIN MENU")
        print("  1. YouTube Shorts Automation")
        print("  2. Quit")

        raw = ask("Select an option")
        try:
            choice = int(raw)
        except ValueError:
            error("Invalid input.")
            continue

        if choice == 1:
            account = _manage_account_interactive()
            if account:
                _youtube_menu(account)
        elif choice == 2:
            info("Goodbye!")
            break
        else:
            error("Invalid option.")


if __name__ == "__main__":
    main()
