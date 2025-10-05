"""Pytest configuration for Frets on Fire tests."""
import os
import warnings

import pytest

from src.fretsonfire import Log


# Ensure SDL uses headless backends during the test run.
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")


# Silence third-party deprecation warnings from pygame internals.
warnings.filterwarnings(
    "ignore",
    message="pkg_resources is deprecated as an API.*",
    category=UserWarning,
    module="pygame.pkgdata",
)


@pytest.fixture(autouse=True)
def configure_logging(tmp_path):
    Log.configure(log_path=tmp_path / "fretsonfire.log", quiet=True, console=False)
    yield
