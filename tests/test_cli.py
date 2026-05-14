import sys

from ascii_art_generator import cli


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

    try:
        cli.main()
    except SystemExit as exc:
        assert exc.code == 2
    else:
        raise AssertionError("Expected video mode without --output-dir to fail")
