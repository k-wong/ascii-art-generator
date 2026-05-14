"""Image and video conversion utilities for ASCII art generation."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from PIL import Image, ImageEnhance, ImageFilter, ImageOps

DEFAULT_CHARSET = "@%#|Oac:*+=-._ "
RESAMPLE_MAP = {
    "nearest": Image.Resampling.NEAREST,
    "bilinear": Image.Resampling.BILINEAR,
    "bicubic": Image.Resampling.BICUBIC,
    "lanczos": Image.Resampling.LANCZOS,
}


@dataclass(frozen=True)
class AsciiOptions:
    """Configuration for converting images to ASCII text."""

    width: int = 240
    height: Optional[int] = None
    charset: str = DEFAULT_CHARSET
    invert: bool = False
    contrast: float = 1.15
    brightness: float = 1.0
    gamma: float = 1.0
    edge_boost: float = 0.0
    scale_y: float = 0.5
    autocontrast: bool = True
    quantize_mode: str = "round"
    resample: str = "lanczos"


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def _validate_options(options: AsciiOptions) -> None:
    if options.width < 8:
        raise ValueError("width must be >= 8")
    if options.height is not None and options.height < 1:
        raise ValueError("height must be >= 1")
    if len(options.charset) < 2:
        raise ValueError("charset must contain at least 2 characters")
    if options.scale_y <= 0:
        raise ValueError("scale_y must be > 0")
    if options.quantize_mode not in {"round", "floor"}:
        raise ValueError("quantize_mode must be one of: round, floor")
    if options.resample not in RESAMPLE_MAP:
        raise ValueError("resample must be one of: nearest, bilinear, bicubic, lanczos")


def image_to_ascii_from_image(
    img: Image.Image,
    options: AsciiOptions | None = None,
    charset: str | None = None,
    **overrides: object,
) -> str:
    """Convert a Pillow image object to ASCII art text.

    Args:
        img: Source Pillow image.
        options: Optional base conversion options.
        charset: Optional custom charset string ordered from darkest to lightest.
        **overrides: Option values to override, for example ``width=120``.
    """
    base_options = options or AsciiOptions()
    if charset is not None:
        overrides["charset"] = charset
    if overrides:
        base_options = AsciiOptions(**{**base_options.__dict__, **overrides})
    _validate_options(base_options)

    img = ImageOps.exif_transpose(img)
    grayscale = img.convert("L")
    src_w, src_h = grayscale.size
    target_w = base_options.width
    target_h = base_options.height or max(1, int((src_h / src_w) * target_w * base_options.scale_y))
    grayscale = grayscale.resize((target_w, target_h), RESAMPLE_MAP[base_options.resample])

    if base_options.contrast != 1.0:
        grayscale = ImageEnhance.Contrast(grayscale).enhance(base_options.contrast)
    if base_options.brightness != 1.0:
        grayscale = ImageEnhance.Brightness(grayscale).enhance(base_options.brightness)
    if base_options.gamma != 1.0:
        inv_gamma = 1.0 / _clamp(base_options.gamma, 0.1, 5.0)
        lut = [int((i / 255.0) ** inv_gamma * 255.0) for i in range(256)]
        grayscale = grayscale.point(lut)
    if base_options.autocontrast:
        grayscale = ImageOps.autocontrast(grayscale)
    if base_options.edge_boost > 0:
        edge_boost = _clamp(base_options.edge_boost, 0.0, 3.0)
        edges = grayscale.filter(ImageFilter.FIND_EDGES)
        grayscale = Image.blend(grayscale, edges, alpha=min(0.85, edge_boost / 3.0))

    pixels = list(grayscale.getdata())
    if base_options.invert:
        pixels = [255 - p for p in pixels]

    last_index = len(base_options.charset) - 1
    chars = []
    for pixel in pixels:
        scaled = (pixel / 255.0) * last_index
        index = round(scaled) if base_options.quantize_mode == "round" else int(scaled)
        chars.append(base_options.charset[max(0, min(last_index, index))])

    return "\n".join(
        "".join(chars[i : i + target_w])
        for i in range(0, len(chars), target_w)
    )


def image_to_ascii(
    image_path: str | Path,
    options: AsciiOptions | None = None,
    charset: str | None = None,
    **overrides: object,
) -> str:
    """Convert an image file to ASCII art text."""
    with Image.open(image_path) as img:
        return image_to_ascii_from_image(img, options=options, charset=charset, **overrides)


def video_to_ascii_frames(
    video_path: str | Path,
    frames_per_second: float = 8.0,
    total_output_frames: int = 32,
    options: AsciiOptions | None = None,
    output_dir: str | Path | None = None,
    frame_prefix: str = "frame",
    charset: str | None = None,
    **overrides: object,
) -> list[str]:
    """Convert a video clip into sampled ASCII frames starting from t=0."""
    if frames_per_second <= 0:
        raise ValueError("frames_per_second must be > 0")
    if total_output_frames <= 0:
        raise ValueError("total_output_frames must be > 0")

    try:
        import imageio.v2 as imageio
    except ImportError as exc:
        raise ImportError(
            "video_to_ascii_frames requires imageio and imageio-ffmpeg. "
            "Install with: python -m pip install 'ascii-art-generator[video]'"
        ) from exc

    reader = imageio.get_reader(str(video_path), "ffmpeg")
    ascii_frames: list[str] = []
    try:
        metadata = reader.get_meta_data()
        source_fps = float(metadata.get("fps", 0.0) or 0.0)
        step = (source_fps / frames_per_second) if source_fps > 0 else 1.0

        for output_index in range(total_output_frames):
            frame_index = int(round(output_index * step))
            try:
                frame_array = reader.get_data(frame_index)
            except IndexError:
                break

            frame_img = Image.fromarray(frame_array)
            ascii_frames.append(
                image_to_ascii_from_image(
                    frame_img,
                    options=options,
                    charset=charset,
                    **overrides,
                )
            )
    finally:
        reader.close()

    if output_dir is not None:
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        for index, frame in enumerate(ascii_frames):
            save_ascii(frame, output_path / f"{frame_prefix}_{index:04d}.txt")

    return ascii_frames


def save_ascii(ascii_art: str, output_path: str | Path) -> None:
    """Save ASCII art to a UTF-8 text file."""
    Path(output_path).write_text(ascii_art, encoding="utf-8")


def _escape_template_literal(value: str) -> str:
    return value.replace("\\", "\\\\").replace("`", "\\`").replace("${", "\\${")


def save_ascii_js(
    ascii_art: str,
    output_path: str | Path,
    variable_name: str = "ASCII_ART",
) -> None:
    """Save ASCII art as a browser global for static websites."""
    escaped = _escape_template_literal(ascii_art)
    js = "// Generated by ascii-art-generator\n" f"window.{variable_name} = `{escaped}`;\n"
    Path(output_path).write_text(js, encoding="utf-8")


def save_ascii_frames_js(
    frames: list[str],
    output_path: str | Path,
    variable_name: str = "ASCII_VIDEO_FRAMES",
) -> None:
    """Save ASCII video frames as a browser global for static websites."""
    escaped_frames = [_escape_template_literal(frame) for frame in frames]
    lines = ["// Generated by ascii-art-generator", f"window.{variable_name} = ["]
    lines.extend([f"  `{frame}`," for frame in escaped_frames])
    lines.append("];")
    Path(output_path).write_text("\n".join(lines) + "\n", encoding="utf-8")
