from termcolor import colored
from typing import Callable, Optional

_log_callback: Optional[Callable[[str, str], None]] = None


def set_log_callback(callback: Optional[Callable[[str, str], None]]) -> None:
    global _log_callback
    _log_callback = callback


def _emit(level: str, message: str) -> None:
    if _log_callback:
        _log_callback(level, message)


def error(message: str) -> None:
    print(colored(f"[ERROR] {message}", "red"))
    _emit("error", message)


def success(message: str) -> None:
    print(colored(f"[OK] {message}", "green"))
    _emit("success", message)


def info(message: str) -> None:
    print(colored(f"[INFO] {message}", "magenta"))
    _emit("info", message)


def warning(message: str) -> None:
    print(colored(f"[WARN] {message}", "yellow"))
    _emit("warning", message)


def header(message: str) -> None:
    print(colored(f"\n{'=' * 40}", "cyan"))
    print(colored(f"  {message}", "cyan"))
    print(colored(f"{'=' * 40}\n", "cyan"))
    _emit("info", f"{'=' * 40}\n  {message}\n{'=' * 40}")


def ask(message: str) -> str:
    return input(colored(f">> {message}: ", "magenta")).strip()
