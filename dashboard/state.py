"""Helpers for initializing and updating Streamlit session state."""

from __future__ import annotations

from typing import Any


def initialize_state(session_state: Any) -> None:
    """Initialize dashboard keys without overwriting an existing conversation."""
    defaults = {
        "messages": [],
        "last_route": None,
        "loading": False,
        "error": None,
        "show_metro": True,
        "show_encicla": True,
    }
    for key, value in defaults.items():
        if key not in session_state:
            session_state[key] = value.copy() if isinstance(value, (list, dict)) else value


def add_message(session_state: Any, role: str, content: str, **metadata: Any) -> None:
    session_state.messages.append({"role": role, "content": content, **metadata})


def clear_conversation(session_state: Any) -> None:
    session_state.messages = []
    session_state.last_route = None
    session_state.error = None

