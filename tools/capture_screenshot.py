"""Capture a Frets on Fire gameplay screenshot for CI artifacts."""
from __future__ import annotations

import argparse
import base64
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


MAX_COMMENT_BASE64 = 64_000
MIN_COMMENT_WIDTH = 120
COMMENT_SCALE_FACTOR = 0.75


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
        "--comment-markdown",
        type=Path,
        default=None,
        help=(
            "Optional path for a Markdown file that inlines the preview image for "
            "posting to pull requests. Requires --comment-output."
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
    comment_markdown: Path | None = None,
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

    if comment_markdown is not None and comment_output is None:
        raise ValueError("--comment-markdown requires --comment-output to be set")

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

        current_surface = preview
        encoded_preview: str | None = None

        while True:
            pygame.image.save(current_surface, comment_output.as_posix())
            data = comment_output.read_bytes()

            if comment_markdown is None:
                break

            encoded_preview = base64.b64encode(data).decode("ascii")
            if len(encoded_preview) <= MAX_COMMENT_BASE64 or current_surface.get_width() <= MIN_COMMENT_WIDTH:
                break

            new_width = max(
                MIN_COMMENT_WIDTH,
                int(round(current_surface.get_width() * COMMENT_SCALE_FACTOR)),
            )
            if new_width == current_surface.get_width():
                break

            new_height = max(
                1,
                int(round(current_surface.get_height() * new_width / current_surface.get_width())),
            )
            current_surface = pygame.transform.smoothscale(
                current_surface,
                (new_width, new_height),
            )

        if comment_markdown is not None:
            if encoded_preview is None:
                encoded_preview = base64.b64encode(comment_output.read_bytes()).decode("ascii")

            comment_markdown = comment_markdown.resolve()
            comment_markdown.parent.mkdir(parents=True, exist_ok=True)
            comment_width = current_surface.get_width()
            comment_markdown.write_text(
                (
                    "🕹️ **Gameplay preview**\n"
                    "Screenshot generated by CI:\n\n"
                    f'<img alt="Frets on Fire gameplay preview" width="{comment_width}" '
                    f'src="data:image/jpeg;base64,{encoded_preview}" />\n\n'
                    "_Full-resolution download available in the `gameplay-screenshot` artifact._\n"
                ),
                encoding="utf-8",
            )


def capture(
    *,
    delay: float,
    output: Path,
    comment_output: Path | None,
    comment_markdown: Path | None,
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
            comment_markdown=comment_markdown,
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
            comment_markdown=args.comment_markdown,
            comment_max_width=args.comment_max_width,
        )
    except Exception as exc:  # pragma: no cover - exercised in CI
        print(f"Failed to capture screenshot: {exc}", file=sys.stderr)
        return 1

    print(f"Screenshot saved to {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
