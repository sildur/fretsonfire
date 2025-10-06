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

try:
    from OpenGL import GL
except Exception:  # pragma: no cover - import varies by environment
    GL = None


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
        help="Path where the full-resolution screenshot will be written",
    )
    parser.add_argument(
        "--comment-output",
        type=Path,
        default=None,
        help=(
            "Optional path for a resized JPEG preview that can be embedded in a PR "
            "comment."
        ),
    )
    parser.add_argument(
        "--comment-max-width",
        type=int,
        default=640,
        metavar="PIXELS",
        help=(
            "Maximum width for the PR comment preview image (default: 640). "
            "Ignored when --comment-output is not provided."
        ),
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


def _save_current_frame(
    output: Path,
    *,
    comment_output: Path | None = None,
    comment_max_width: int = 640,
) -> None:
    surface = pygame.display.get_surface()
    if surface is None:
        raise RuntimeError("No display surface available for screenshot capture")

    width, height = surface.get_size()
    flags = surface.get_flags()

    if flags & pygame.OPENGL:
        if GL is None:
            raise RuntimeError("OpenGL capture requested but PyOpenGL is unavailable")

        # Ensure tightly packed pixel rows before reading from the framebuffer.
        GL.glPixelStorei(GL.GL_PACK_ALIGNMENT, 1)

        pixel_data = GL.glReadPixels(0, 0, width, height, GL.GL_RGBA, GL.GL_UNSIGNED_BYTE)
        if pixel_data is None:
            raise RuntimeError("Failed to read OpenGL framebuffer for screenshot")

        if not isinstance(pixel_data, (bytes, bytearray, memoryview)):
            pixel_data = bytes(pixel_data)

        image = pygame.image.frombuffer(pixel_data, (width, height), "RGBA")
        # OpenGL's origin is the bottom-left; flip vertically to match usual screenshots.
        image = pygame.transform.flip(image, False, True).copy()
    else:
        image = surface.copy()

    output.parent.mkdir(parents=True, exist_ok=True)
    pygame.image.save(image, output.as_posix())

    if comment_output is not None:
        preview = image

        if comment_max_width > 0 and preview.get_width() > comment_max_width:
            scale = comment_max_width / preview.get_width()
            new_size = (
                comment_max_width,
                max(1, int(round(preview.get_height() * scale))),
            )
            preview = pygame.transform.smoothscale(preview, new_size)

        if preview.get_flags() & pygame.SRCALPHA:
            preview = preview.convert(24)

        comment_output = comment_output.resolve()
        comment_output.parent.mkdir(parents=True, exist_ok=True)
        pygame.image.save(preview, comment_output.as_posix())


def capture(
    *,
    delay: float,
    output: Path,
    comment_output: Path | None,
    comment_max_width: int,
) -> Path:
    Log.set_quiet(True)

    config = Config.load(Version.appName() + ".ini", setAsDefault=True)
    engine = GameEngine(config)
    engine.setStartupLayer(MainMenu(engine))

    try:
        wait_for_frame(engine, delay)
        output = output.resolve()
        _save_current_frame(
            output,
            comment_output=comment_output,
            comment_max_width=comment_max_width,
        )
        return output
    finally:
        engine.quit()
        pygame.quit()


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    try:
        output_path = capture(
            delay=args.delay,
            output=args.output,
            comment_output=args.comment_output,
            comment_max_width=args.comment_max_width,
        )
    except Exception as exc:  # pragma: no cover - exercised in CI
        print(f"Failed to capture screenshot: {exc}", file=sys.stderr)
        return 1

    print(f"Screenshot saved to {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
