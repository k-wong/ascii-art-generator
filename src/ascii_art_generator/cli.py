"""Command-line interface for ascii-art-generator."""

from __future__ import annotations

import argparse
from pathlib import Path

from ascii_art_generator.converter import (
    DEFAULT_CHARSET,
    AsciiOptions,
    image_to_ascii,
    save_ascii,
    save_ascii_frames_js,
    save_ascii_js,
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
        "--autocontrast",
        action="store_true",
        default=True,
        help="Enable autocontrast",
    )
    parser.add_argument(
        "--no-autocontrast",
        dest="autocontrast",
        action="store_false",
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


def _build_image_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Convert an image to ASCII art.")
    parser.add_argument("input", help="Input image path")
    parser.add_argument("-o", "--output", help="Output text file path")
    _add_ascii_options(parser)
    parser.add_argument(
        "--compare-to",
        help="Optional expected ASCII file. Prints exact character match ratio.",
    )
    parser.add_argument("--print", action="store_true", help="Print ASCII art to terminal")
    parser.add_argument("--output-js", help="Optional JS output path that writes window.ASCII_ART.")
    parser.add_argument(
        "--js-variable",
        default="ASCII_ART",
        help="Browser global variable name for --output-js.",
    )
    return parser


def _build_video_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Convert a video to sampled ASCII art frames.")
    parser.add_argument("input", help="Input video path")
    parser.add_argument(
        "-d",
        "--output-dir",
        required=True,
        help="Directory for generated per-frame .txt files.",
    )
    parser.add_argument("--fps", type=float, default=8.0, help="Sampling FPS from the source video")
    parser.add_argument(
        "--frames",
        type=int,
        default=32,
        help="Maximum number of ASCII frames to generate",
    )
    parser.add_argument("--frame-prefix", default="frame", help="Prefix for generated frame files")
    parser.add_argument(
        "--output-js",
        help="Optional JS output path that writes all frames to window.ASCII_VIDEO_FRAMES.",
    )
    parser.add_argument(
        "--js-variable",
        default="ASCII_VIDEO_FRAMES",
        help="Browser global variable name for --output-js.",
    )
    _add_ascii_options(parser)
    return parser


def _similarity(a: str, b: str) -> float:
    total = max(len(a), len(b))
    if total == 0:
        return 1.0
    min_len = min(len(a), len(b))
    matches = sum(1 for index in range(min_len) if a[index] == b[index])
    return matches / total


def main() -> None:
    args = _build_image_parser().parse_args()
    options = _options_from_args(args)
    ascii_art = image_to_ascii(args.input, options=options)

    if args.output:
        save_ascii(ascii_art, args.output)
        print(f"Saved ASCII art to: {args.output}")
    if args.output_js:
        save_ascii_js(ascii_art, args.output_js, variable_name=args.js_variable)
        print(f"Saved JS ASCII data to: {args.output_js}")

    if args.compare_to:
        expected = Path(args.compare_to).read_text(encoding="utf-8")
        print(f"Exact character match: {_similarity(ascii_art, expected):.4%}")

    if args.print or (not args.output and not args.output_js):
        print(ascii_art)


def main_video() -> None:
    args = _build_video_parser().parse_args()
    options = _options_from_args(args)
    frames = video_to_ascii_frames(
        args.input,
        frames_per_second=args.fps,
        total_output_frames=args.frames,
        options=options,
        output_dir=args.output_dir,
        frame_prefix=args.frame_prefix,
    )
    print(f"Saved {len(frames)} ASCII frame(s) to: {args.output_dir}")

    if args.output_js:
        save_ascii_frames_js(frames, args.output_js, variable_name=args.js_variable)
        print(f"Saved JS ASCII frame data to: {args.output_js}")


if __name__ == "__main__":
    main()
