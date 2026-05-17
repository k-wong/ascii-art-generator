# ASCII Art Generator

A small Python library and CLI for converting images and videos into ASCII art, with customizable styling.

## Demo

<img width="1204" height="778" alt="Screenshot 2026-05-14 at 8 32 22 AM" src="https://github.com/user-attachments/assets/f0c087ef-a68d-4606-b7f1-11c92b075023" />

## Features

- Convert image files to ASCII text.
- Sample videos into ASCII frames, and set your desired FPS and total frames/animation length (starts from 0:00).
- Tune width, height, contrast, brightness, gamma, edge boost, character set, and resize kernel.
- Auto-contrast built in for great default results.
- Use as a command-line tool or import as a Python library.

## Requirements

- Python 3.9 or newer
- pip with PEP 517 / `pyproject.toml` build support
- setuptools 68 or newer

## Installation

1. Clone/download this repo
2. Navigate to the local folder and run the below:
```bash
python3 -m pip install .
or
python -m pip install .
```

## CLI Usage

```bash
ascii-art input.jpg --output output.txt --width 160
```

Use a custom character set by passing characters from darkest to lightest:

```bash
ascii-art input.jpg --width 120 --charset "@#*+=-. " --print
```

Print directly to the terminal:

```bash
ascii-art input.jpg --width 120 --print
```

Generate ASCII frames from a video:

```bash
ascii-art -v input.mp4 --output-dir frames --fps 8 --frames 120 --width 120
```

## Python Usage

```python
from ascii_art_generator import AsciiOptions, image_to_ascii

ascii_art = image_to_ascii(
    "input.jpg",
    options=AsciiOptions(width=120, charset="@%#*+=-:. "),
)

print(ascii_art)
```

You can also pass a charset string as a keyword override when you do not need a full
`AsciiOptions` object:

```python
from ascii_art_generator import image_to_ascii

ascii_art = image_to_ascii("input.jpg", width=120, charset="01")
```

If you already have a Pillow image:

```python
from PIL import Image
from ascii_art_generator import image_to_ascii_from_image

image = Image.open("input.jpg")
ascii_art = image_to_ascii_from_image(image, width=120)
```


## License

MIT
