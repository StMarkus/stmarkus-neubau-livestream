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
        description="Build HLS playlist from captured images (weekly or all)."
    )
    parser.add_argument("--images-dir", default=env("IMAGES_DIR", "./images"))
    parser.add_argument("--output-dir", default=env("HLS_DIR", "./hls"))
    parser.add_argument(
        "--playlist",
        default=env("HLS_PLAYLIST", "stream.m3u8"),
        help="Playlist filename (default: stream.m3u8).",
    )
    parser.add_argument("--fps", default=env("VIDEO_FPS", "2"))
    parser.add_argument(
        "--range",
        choices=["week", "all"],
        default=env("HLS_RANGE", "week"),
        help="Which images to include (default: week).",
    )
    parser.add_argument("--timezone", default=env("TIMEZONE", "Europe/Berlin"))
    parser.add_argument(
        "--segment-time",
        default=env("HLS_SEGMENT_TIME", "4"),
        help="Segment duration in seconds.",
    )
    parser.add_argument(
        "--list-size",
        default=env("HLS_LIST_SIZE", "0"),
        help="0 keeps the full playlist.",
    )
    parser.add_argument(
        "--playlist-type",
        default=env("HLS_PLAYLIST_TYPE", "vod"),
        choices=["vod", "event"],
    )
    parser.add_argument(
        "--no-clean",
        action="store_true",
        help="Do not delete old segments before rebuild.",
    )
    args = parser.parse_args()

    images_dir = Path(args.images_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    playlist_path = Path(args.playlist)
    if not playlist_path.is_absolute():
        playlist_path = output_dir / playlist_path

    if not args.no_clean:
        for old in output_dir.glob("segment_*.ts"):
            old.unlink(missing_ok=True)
        playlist_path.unlink(missing_ok=True)

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

    segment_template = output_dir / "segment_%05d.ts"

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
        "-hls_time",
        str(args.segment_time),
        "-hls_list_size",
        str(args.list_size),
        "-hls_playlist_type",
        args.playlist_type,
        "-hls_flags",
        "independent_segments",
        "-hls_segment_filename",
        str(segment_template),
        "-f",
        "hls",
        str(playlist_path),
    ]

    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as exc:
        print(f"ffmpeg failed: {exc}", file=sys.stderr)
        return 3
    finally:
        Path(list_path).unlink(missing_ok=True)

    print(str(playlist_path))
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
