"""Ollama LLM provider with retry logic and error handling."""

import ollama as _ollama

from typing import Optional

from src.config import get_ollama_base_url
from src.status import warning

_selected_model: Optional[str] = None
_client: Optional[_ollama.Client] = None


def _get_client() -> _ollama.Client:
    global _client
    if _client is None:
        _client = _ollama.Client(host=get_ollama_base_url())
    return _client


def list_models() -> list[str]:
    """List all models available on the local Ollama server."""
    response = _get_client().list()
    return sorted(m.model for m in response.models)


def select_model(model: str) -> None:
    """Set the model to use for all subsequent generate_text calls."""
    global _selected_model
    _selected_model = model


def get_active_model() -> Optional[str]:
    return _selected_model


def generate_text(prompt: str, model_name: Optional[str] = None, max_retries: int = 1) -> str:
    """Generate text using the local Ollama server with retry logic."""
    model = model_name or _selected_model
    if not model:
        raise RuntimeError("No Ollama model selected. Call select_model() first or pass model_name.")

    last_error: Optional[Exception] = None

    for attempt in range(1, max_retries + 1):
        try:
            response = _get_client().chat(
                model=model,
                messages=[{"role": "user", "content": prompt}],
            )
            content = response["message"]["content"].strip()
            if content:
                return content
            warning(f"LLM returned empty response (attempt {attempt}/{max_retries})")
        except Exception as e:
            last_error = e
            warning(f"LLM call failed (attempt {attempt}/{max_retries}): {e}")

    raise RuntimeError(f"Failed to generate text after {max_retries} attempts: {last_error}")
