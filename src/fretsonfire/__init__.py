"""Frets on Fire game package."""
from __future__ import annotations

import sys
from importlib import import_module
from pathlib import Path

_pkg_root = Path(__file__).resolve().parent
if str(_pkg_root) not in sys.path:
    sys.path.insert(0, str(_pkg_root))

try:
    __version__ = import_module(".Version", __name__).version()
except Exception:  # pragma: no cover - metadata only
    __version__ = "0.0.dev0"

__all__ = []

