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
        "--preview-output",
        type=Path,
        help="Optional path for a scaled-down JPEG preview",
    )
    parser.add_argument(
        "--preview-width",
        type=int,
        default=640,
        help="Width in pixels for the preview image when --preview-output is set",
    )
    parser.add_argument(
        "--preview-max-bytes",
        type=int,
        default=1_000_000,
        help=(
            "Maximum allowed size for the preview (in bytes). If the encoded file "
            "is larger, the helper resizes the preview until it fits or the "
            "dimensions reach a practical minimum."
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


def _capture_current_frame() -> pygame.Surface:
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

    return image


def _save_image(image: pygame.Surface, path: Path) -> Path:
    path = path.resolve()
    path.parent.mkdir(parents=True, exist_ok=True)

    suffix = path.suffix.lower()
    if suffix in {".jpg", ".jpeg"}:
        # JPEG does not support an alpha channel; convert to 24-bit RGB if needed.
        masks = image.get_masks()
        has_alpha = len(masks) == 4 and masks[3] != 0
        if has_alpha:
            image = image.convert(24)

    pygame.image.save(image, path.as_posix())
    return path


def _scale_surface(surface: pygame.Surface, width: int) -> pygame.Surface:
    width = max(1, width)
    original_width, original_height = surface.get_size()
    if width >= original_width:
        return surface.copy()

    height = max(1, int(original_height * (width / original_width)))
    return pygame.transform.smoothscale(surface, (width, height))


def _write_preview(
    frame: pygame.Surface,
    *,
    output: Path,
    width: int,
    max_bytes: int,
) -> None:
    preview = _scale_surface(frame, width)
    saved = _save_image(preview, output)

    if max_bytes <= 0:
        return

    try:
        current_size = saved.stat().st_size
    except OSError as error:  # pragma: no cover - filesystem errors are unlikely
        raise RuntimeError(f"Unable to stat preview file {saved}: {error}") from error

    if current_size <= max_bytes:
        return

    min_edge = 64
    shrink_factor = 0.75
    width = preview.get_width()

    while current_size > max_bytes and width > min_edge:
        width = max(min_edge, int(width * shrink_factor))
        preview = _scale_surface(frame, width)
        saved = _save_image(preview, output)
        current_size = saved.stat().st_size

    if current_size > max_bytes:
        raise RuntimeError(
            "Preview screenshot exceeds size budget even after downscaling: "
            f"{current_size} bytes > {max_bytes} bytes"
        )



def capture(
    *,
    delay: float,
    output: Path,
    preview_output: Path | None,
    preview_width: int,
    preview_max_bytes: int,
) -> Path:
    Log.set_quiet(True)

    config = Config.load(Version.appName() + ".ini", setAsDefault=True)
    engine = GameEngine(config)
    engine.setStartupLayer(MainMenu(engine))

    try:
        wait_for_frame(engine, delay)
        frame = _capture_current_frame()
        output_path = _save_image(frame, output)

        if preview_output is not None:
            _write_preview(
                frame,
                output=preview_output,
                width=preview_width,
                max_bytes=max(0, preview_max_bytes),
            )

        return output_path
    finally:
        engine.quit()
        pygame.quit()


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    try:
        output_path = capture(
            delay=args.delay,
            output=args.output,
            preview_output=args.preview_output,
            preview_width=args.preview_width,
            preview_max_bytes=args.preview_max_bytes,
        )
    except Exception as exc:  # pragma: no cover - exercised in CI
        print(f"Failed to capture screenshot: {exc}", file=sys.stderr)
        return 1

    print(f"Screenshot saved to {output_path}")
    if args.preview_output is not None:
        print(f"Preview saved to {Path(args.preview_output).resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
