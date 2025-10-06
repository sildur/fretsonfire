"""Capture a Frets on Fire gameplay screenshot for CI artifacts."""
from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path

# Ensure pygame uses a dummy audio driver so CI environments without sound
# hardware do not error during initialization. This must be set before the
# GameEngine module imports pygame.
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
# Remove any lingering dummy video driver so we can connect to the XVFB display.
os.environ.pop("SDL_VIDEODRIVER", None)

from fretsonfire import Config, Log, Version
from fretsonfire.GameEngine import GameEngine
from fretsonfire.MainMenu import MainMenu

import pygame


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Launch Frets on Fire, wait a bit for the main menu to render, "
            "and save the current frame to disk."
        )
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=5.0,
        help="Seconds to wait before capturing the screenshot (default: 5)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("artifacts/gameplay.png"),
        help="Path where the screenshot will be written",
    )
    return parser.parse_args(argv)


def wait_for_frame(engine: GameEngine, delay: float) -> None:
    """Run the engine loop until *delay* seconds have elapsed."""
    start = time.monotonic()
    deadline = start + max(0.0, delay)

    # Run the engine for at least one frame to ensure the menu renders.
    if not engine.run():
        raise RuntimeError("Game engine stopped before rendering a frame")

    while time.monotonic() < deadline:
        if not engine.run():
            break


def capture(delay: float, output: Path) -> Path:
    Log.set_quiet(True)

    config = Config.load(Version.appName() + ".ini", setAsDefault=True)
    engine = GameEngine(config)
    engine.setStartupLayer(MainMenu(engine))

    try:
        wait_for_frame(engine, delay)

        surface = pygame.display.get_surface()
        if surface is None:
            raise RuntimeError("No display surface available for screenshot capture")

        output = output.resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        pygame.image.save(surface, output.as_posix())
        return output
    finally:
        engine.quit()
        pygame.quit()


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    try:
        output_path = capture(delay=args.delay, output=args.output)
    except Exception as exc:  # pragma: no cover - exercised in CI
        print(f"Failed to capture screenshot: {exc}", file=sys.stderr)
        return 1

    print(f"Screenshot saved to {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
