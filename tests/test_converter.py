from PIL import Image

from ascii_art_generator import (
    AsciiOptions,
    image_to_ascii,
    image_to_ascii_from_image,
)


def test_image_to_ascii_from_image_uses_requested_dimensions() -> None:
    image = Image.new("L", (4, 4), color=128)

    result = image_to_ascii_from_image(
        image,
        options=AsciiOptions(width=8, height=4, charset=" .", autocontrast=False),
    )

    lines = result.splitlines()
    assert len(lines) == 4
    assert all(len(line) == 8 for line in lines)


def test_image_to_ascii_from_image_supports_custom_charset() -> None:
    image = Image.new("L", (8, 2), color=255)

    result = image_to_ascii_from_image(
        image,
        options=AsciiOptions(width=8, height=1, charset="ab", autocontrast=False),
    )

    assert result == "bbbbbbbb"


def test_image_to_ascii_from_image_supports_charset_override() -> None:
    image = Image.new("L", (8, 2), color=0)

    result = image_to_ascii_from_image(
        image,
        width=8,
        height=1,
        charset="01",
        autocontrast=False,
    )

    assert result == "00000000"


def test_image_to_ascii_applies_exif_orientation(tmp_path) -> None:
    image = Image.new("L", (4, 8), color=255)
    exif = Image.Exif()
    exif[274] = 6
    image_path = tmp_path / "oriented.jpg"
    image.save(image_path, exif=exif)

    result = image_to_ascii(
        image_path,
        options=AsciiOptions(width=8, charset=" .", autocontrast=False),
    )

    assert len(result.splitlines()) == 2
