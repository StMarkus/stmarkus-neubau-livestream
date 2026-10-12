#!/usr/bin/env python3
import argparse
import datetime as dt
import os
from pathlib import Path
import subprocess
import sys
from tempfile import NamedTemporaryFile
from zoneinfo import ZoneInfo


def env(name: str, default: str) -> str:
    return os.getenv(name, default)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build MP4 from captured images (weekly or all)."
    )
    parser.add_argument("--images-dir", default=env("IMAGES_DIR", "./images"))
    parser.add_argument("--videos-dir", default=env("VIDEOS_DIR", "./videos"))
    parser.add_argument("--fps", default=env("VIDEO_FPS", "2"))
    parser.add_argument(
        "--output",
        default=env("VIDEO_OUTPUT", ""),
        help="Output filename or path (default: week.mp4 or all.mp4).",
    )
    parser.add_argument(
        "--range",
        choices=["week", "all"],
        default=env("VIDEO_RANGE", "week"),
        help="Which images to include (default: week).",
    )
    parser.add_argument("--timezone", default=env("TIMEZONE", "Europe/Berlin"))
    args = parser.parse_args()

    images_dir = Path(args.images_dir)
    videos_dir = Path(args.videos_dir)
    videos_dir.mkdir(parents=True, exist_ok=True)

    output_name = args.output.strip()
    if not output_name:
        output_name = "week.mp4" if args.range == "week" else "all.mp4"

    output_path = Path(output_name)
    output = output_path if output_path.is_absolute() else videos_dir / output_path

    images = sorted(images_dir.glob("image_*.jpg"))
    if args.range == "week":
        now = dt.datetime.now(ZoneInfo(args.timezone)).date()
        week_start = now - dt.timedelta(days=now.weekday())
        week_end = week_start + dt.timedelta(days=6)
        images = [
            image
            for image in images
            if _date_in_range(image, week_start, week_end)
        ]
    if not images:
        scope = "current week" if args.range == "week" else "all"
        print(f"No images found for {scope} in {images_dir}", file=sys.stderr)
        return 2

    with NamedTemporaryFile("w", delete=False) as list_file:
        for image in images:
            list_file.write(f"file '{image.resolve()}'\n")
        list_path = list_file.name

    cmd = [
        "ffmpeg",
        "-y",
        "-hide_banner",
        "-loglevel",
        "error",
        "-r",
        str(args.fps),
        "-f",
        "concat",
        "-safe",
        "0",
        "-i",
        list_path,
        "-vf",
        "format=yuv420p",
        "-movflags",
        "+faststart",
        str(output),
    ]

    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as exc:
        print(f"ffmpeg failed: {exc}", file=sys.stderr)
        return 3
    finally:
        Path(list_path).unlink(missing_ok=True)

    print(str(output))
    return 0


def _date_in_range(path: Path, start: dt.date, end: dt.date) -> bool:
    name = path.stem
    parts = name.split("_")
    if len(parts) < 3:
        return False
    try:
        date_val = dt.datetime.strptime(parts[1], "%Y%m%d").date()
    except ValueError:
        return False
    return start <= date_val <= end


if __name__ == "__main__":
    raise SystemExit(main())
