"""Command-line interface for ascii-art-generator."""

from __future__ import annotations

import argparse
from pathlib import Path

from ascii_art_generator.converter import (
    DEFAULT_CHARSET,
    AsciiOptions,
    image_to_ascii,
    save_ascii,
    video_to_ascii_frames,
)


def _add_ascii_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("-w", "--width", type=int, default=240, help="ASCII width in characters")
    parser.add_argument("--height", type=int, help="ASCII height in characters")
    parser.add_argument(
        "--charset",
        default=DEFAULT_CHARSET,
        help="Custom charset string ordered from darkest to lightest.",
    )
    parser.add_argument("--invert", action="store_true", help="Invert dark/light mapping")
    parser.add_argument("--contrast", type=float, default=1.15, help="Contrast multiplier")
    parser.add_argument("--brightness", type=float, default=1.0, help="Brightness multiplier")
    parser.add_argument("--gamma", type=float, default=1.0, help="Gamma correction")
    parser.add_argument("--edge-boost", type=float, default=0.0, help="Edge emphasis from 0 to 3")
    parser.add_argument(
        "--no-autocontrast",
        dest="autocontrast",
        action="store_false",
        default=True,
        help="Disable autocontrast",
    )
    parser.add_argument(
        "--quantize",
        choices=["round", "floor"],
        default="round",
        help="Luminance quantization mode",
    )
    parser.add_argument(
        "--resample",
        choices=["nearest", "bilinear", "bicubic", "lanczos"],
        default="lanczos",
        help="Image resize kernel",
    )
    parser.add_argument(
        "--scale-y",
        type=float,
        default=0.5,
        help="Height correction factor for character aspect ratio",
    )


def _options_from_args(args: argparse.Namespace) -> AsciiOptions:
    return AsciiOptions(
        width=args.width,
        height=args.height,
        charset=args.charset,
        invert=args.invert,
        contrast=args.contrast,
        brightness=args.brightness,
        gamma=args.gamma,
        edge_boost=args.edge_boost,
        scale_y=args.scale_y,
        autocontrast=args.autocontrast,
        quantize_mode=args.quantize,
        resample=args.resample,
    )


def _add_video_options(parser: argparse.ArgumentParser, output_dir_required: bool = False) -> None:
    parser.add_argument(
        "-d",
        "--output-dir",
        required=output_dir_required,
        help="Directory for generated per-frame .txt files.",
    )
    parser.add_argument("--fps", type=float, help="Sampling FPS from the source video")
    parser.add_argument(
        "--frames",
        type=int,
        help="Maximum number of ASCII frames to generate",
    )
    parser.add_argument("--frame-prefix", help="Prefix for generated frame files")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Convert an image or video to ASCII art.")
    parser.add_argument("input", help="Input image or video path")
    parser.add_argument(
        "-v",
        "--video",
        action="store_true",
        help="Treat input as a video and sample ASCII frames.",
    )
    parser.add_argument("-o", "--output", help="Output text file path")
    _add_ascii_options(parser)
    _add_video_options(parser)
    parser.add_argument(
        "--compare-to",
        help="Optional expected ASCII file. Prints exact character match ratio.",
    )
    parser.add_argument("--print", action="store_true", help="Print ASCII art to terminal")
    return parser


def _similarity(a: str, b: str) -> float:
    total = max(len(a), len(b))
    if total == 0:
        return 1.0
    min_len = min(len(a), len(b))
    matches = sum(1 for index in range(min_len) if a[index] == b[index])
    return matches / total


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()

    if args.video:
        _reject_video_mode_photo_options(parser, args)
        if not args.output_dir:
            parser.error("--output-dir is required with -v/--video")
        _run_video(parser, args, _options_from_args(args))
        return

    _reject_photo_mode_video_options(parser, args)

    try:
        ascii_art = image_to_ascii(args.input, options=_options_from_args(args))

        if args.output:
            save_ascii(ascii_art, args.output)
            print(f"Saved ASCII art to: {args.output}")

        if args.compare_to:
            expected = Path(args.compare_to).read_text(encoding="utf-8")
            print(f"Exact character match: {_similarity(ascii_art, expected):.4%}")

        if args.print or not args.output:
            print(ascii_art)
    except (OSError, ValueError, ImportError, RuntimeError) as exc:
        parser.error(str(exc))


def _reject_photo_mode_video_options(
    parser: argparse.ArgumentParser,
    args: argparse.Namespace,
) -> None:
    invalid_options = []
    if args.output_dir is not None:
        invalid_options.append("--output-dir")
    if args.fps is not None:
        invalid_options.append("--fps")
    if args.frames is not None:
        invalid_options.append("--frames")
    if args.frame_prefix is not None:
        invalid_options.append("--frame-prefix")

    if invalid_options:
        parser.error(f"{', '.join(invalid_options)} can only be used with -v/--video")


def _reject_video_mode_photo_options(
    parser: argparse.ArgumentParser,
    args: argparse.Namespace,
) -> None:
    invalid_options = []
    if args.output is not None:
        invalid_options.append("--output")
    if args.compare_to is not None:
        invalid_options.append("--compare-to")
    if args.print:
        invalid_options.append("--print")

    if invalid_options:
        parser.error(f"{', '.join(invalid_options)} cannot be used with -v/--video")


def _run_video(
    parser: argparse.ArgumentParser,
    args: argparse.Namespace,
    options: AsciiOptions,
) -> None:
    try:
        frames = video_to_ascii_frames(
            args.input,
            frames_per_second=args.fps if args.fps is not None else 8.0,
            total_output_frames=args.frames if args.frames is not None else 32,
            options=options,
            output_dir=args.output_dir,
            frame_prefix=args.frame_prefix or "frame",
        )
        print(f"Saved {len(frames)} ASCII frame(s) to: {args.output_dir}")
    except (OSError, ValueError, ImportError, RuntimeError) as exc:
        parser.error(str(exc))


if __name__ == "__main__":
    main()
