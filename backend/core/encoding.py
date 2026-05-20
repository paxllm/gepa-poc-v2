"""Ensure UTF-8 stdio/logging on Windows for GEPA and LLM output."""

from __future__ import annotations

import os
import sys


def ensure_utf8_environment() -> None:
    """Prefer UTF-8 for console and default text file encoding (Windows cp1252 safe)."""
    os.environ.setdefault("PYTHONUTF8", "1")
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is None:
            continue
        try:
            reconfigure(encoding="utf-8", errors="replace")
        except (OSError, ValueError):
            pass
