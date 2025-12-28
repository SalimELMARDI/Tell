"""Utility functions for tell."""
import json
import os
from pathlib import Path
from typing import List, Dict, Any

# Define where history lives: ~/.tell/history.json
HISTORY_DIR = Path.home() / ".tell"
HISTORY_FILE = HISTORY_DIR / "history.json"
MAX_HISTORY = 10  # Keep last 10 interactions (5 user, 5 assistant)


def load_history() -> List[Dict[str, str]]:
    """Load chat history from the local JSON file."""
    if not HISTORY_FILE.exists():
        return []
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return []


def save_history(messages: List[Dict[str, str]]) -> None:
    """Save the updated chat history, trimming old entries."""
    # Ensure directory exists
    HISTORY_DIR.mkdir(parents=True, exist_ok=True)

    # Keep only the tail (most recent messages)
    trimmed_history = messages[-MAX_HISTORY:]

    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(trimmed_history, f, indent=2)


def clear_history() -> None:
    """Delete the history file."""
    if HISTORY_FILE.exists():
        os.remove(HISTORY_FILE)
