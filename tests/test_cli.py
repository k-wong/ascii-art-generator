import sys

import pytest

from ascii_art_generator import cli


def test_photo_mode_uses_autocontrast_by_default(monkeypatch, capsys) -> None:
    calls = {}

    def fake_image_to_ascii(input_path, options):
        calls["input_path"] = input_path
        calls["autocontrast"] = options.autocontrast
        return "ascii"

    monkeypatch.setattr(cli, "image_to_ascii", fake_image_to_ascii)
    monkeypatch.setattr(sys, "argv", ["ascii-art", "input.jpg"])

    cli.main()

    assert calls == {"input_path": "input.jpg", "autocontrast": True}
    assert "ascii" in capsys.readouterr().out


def test_photo_mode_supports_no_autocontrast(monkeypatch, capsys) -> None:
    calls = {}

    def fake_image_to_ascii(input_path, options):
        calls["input_path"] = input_path
        calls["autocontrast"] = options.autocontrast
        return "ascii"

    monkeypatch.setattr(cli, "image_to_ascii", fake_image_to_ascii)
    monkeypatch.setattr(sys, "argv", ["ascii-art", "input.jpg", "--no-autocontrast"])

    cli.main()

    assert calls == {"input_path": "input.jpg", "autocontrast": False}
    assert "ascii" in capsys.readouterr().out


def test_video_flag_routes_to_video_converter(monkeypatch, tmp_path, capsys) -> None:
    calls = {}

    def fake_video_to_ascii_frames(
        input_path,
        frames_per_second,
        total_output_frames,
        options,
        output_dir,
        frame_prefix,
    ):
        calls["input_path"] = input_path
        calls["frames_per_second"] = frames_per_second
        calls["total_output_frames"] = total_output_frames
        calls["output_dir"] = output_dir
        calls["frame_prefix"] = frame_prefix
        calls["width"] = options.width
        return ["frame"]

    output_dir = tmp_path / "frames"
    monkeypatch.setattr(cli, "video_to_ascii_frames", fake_video_to_ascii_frames)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "ascii-art",
            "-v",
            "input.mp4",
            "--output-dir",
            str(output_dir),
            "--fps",
            "12",
            "--frames",
            "5",
            "--width",
            "80",
        ],
    )

    cli.main()

    assert calls == {
        "input_path": "input.mp4",
        "frames_per_second": 12.0,
        "total_output_frames": 5,
        "output_dir": str(output_dir),
        "frame_prefix": "frame",
        "width": 80,
    }
    assert f"Saved 1 ASCII frame(s) to: {output_dir}" in capsys.readouterr().out


def test_video_flag_requires_output_dir(monkeypatch) -> None:
    monkeypatch.setattr(sys, "argv", ["ascii-art", "-v", "input.mp4"])

    with pytest.raises(SystemExit) as exc_info:
        cli.main()

    assert exc_info.value.code == 2


def test_photo_mode_rejects_video_options(monkeypatch, capsys) -> None:
    monkeypatch.setattr(sys, "argv", ["ascii-art", "input.jpg", "--fps", "12"])

    with pytest.raises(SystemExit) as exc_info:
        cli.main()

    assert exc_info.value.code == 2
    captured = capsys.readouterr()
    assert "--fps can only be used with -v/--video" in captured.err
    assert "Traceback" not in captured.err


def test_video_mode_rejects_photo_options(monkeypatch, tmp_path, capsys) -> None:
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "ascii-art",
            "-v",
            "input.mp4",
            "--output",
            "out.txt",
            "--output-dir",
            str(tmp_path / "frames"),
        ],
    )

    with pytest.raises(SystemExit) as exc_info:
        cli.main()

    assert exc_info.value.code == 2
    captured = capsys.readouterr()
    assert "--output cannot be used with -v/--video" in captured.err
    assert "Traceback" not in captured.err


def test_missing_image_path_exits_without_traceback(monkeypatch, capsys) -> None:
    monkeypatch.setattr(sys, "argv", ["ascii-art", "missing.jpg"])

    with pytest.raises(SystemExit) as exc_info:
        cli.main()

    assert exc_info.value.code == 2
    captured = capsys.readouterr()
    assert "missing.jpg" in captured.err
    assert "Traceback" not in captured.err


def test_missing_video_path_exits_without_traceback(monkeypatch, tmp_path, capsys) -> None:
    monkeypatch.setattr(
        sys,
        "argv",
        ["ascii-art", "-v", "missing.mp4", "--output-dir", str(tmp_path / "frames")],
    )

    with pytest.raises(SystemExit) as exc_info:
        cli.main()

    assert exc_info.value.code == 2
    captured = capsys.readouterr()
    assert "missing.mp4" in captured.err
    assert "Traceback" not in captured.err
