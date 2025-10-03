"""Pytest configuration for Frets on Fire tests."""
import os

# Ensure SDL uses headless backends during the test run.
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

