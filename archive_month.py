#!/usr/bin/env python3
"""Archiviert alle Fotos eines Monats in Google Drive (via rclone).

Ablauf:
1. Fotos des Monats mit rclone nach Drive kopieren
2. Upload per rclone check verifizieren
3. Alle Fotos des Monats außer 14:00 Uhr aus images/ entfernen
4. gh-pages-Branch als einzelnen neuen Commit neu aufbauen und force-pushen,
   damit die Git-Historie (und das Repo) nicht mit den Originalen wächst
"""
import argparse
import datetime as dt
import fcntl
import os
import subprocess
import sys
from pathlib import Path
from zoneinfo import ZoneInfo


def run(*cmd: str) -> None:
    subprocess.run(cmd, check=True)


def previous_month(tz_name: str) -> str:
    first = dt.datetime.now(ZoneInfo(tz_name)).replace(day=1)
    return (first - dt.timedelta(days=1)).strftime("%Y-%m")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--month", help="YYYY-MM (default: Vormonat)")
    parser.add_argument("--images-dir", default=os.getenv("IMAGES_DIR", "./images"))
    parser.add_argument(
        "--remote",
        default=os.getenv("DRIVE_REMOTE", "gdrive:Neubau-Livestream"),
        help="rclone-Ziel ohne Monatsordner",
    )
    parser.add_argument("--keep", default="1400", help="HHMM, das im Repo bleibt")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    month = args.month or previous_month(os.getenv("TIMEZONE", "Europe/Berlin"))
    images_dir = Path(args.images_dir).resolve()
    stamp = month.replace("-", "")
    include = f"image_{stamp}??_????.jpg"
    files = sorted(images_dir.glob(include))
    if not files:
        print(f"Keine Fotos für {month} gefunden", file=sys.stderr)
        return 1

    target = f"{args.remote}/{month}"
    print(f"{len(files)} Fotos -> {target}")
    if args.dry_run:
        return 0

    # Gleiches Lockfile wie publish_images.sh, damit kein Push dazwischenfunkt
    repo = images_dir.parent
    lock = open(repo / ".publish.lock", "w")
    fcntl.flock(lock, fcntl.LOCK_EX)

    run("rclone", "copy", str(images_dir), target, "--include", include, "--checksum")
    run("rclone", "check", str(images_dir), target, "--include", include, "--one-way")

    keep_suffix = f"_{args.keep}.jpg"
    for f in files:
        if not f.name.endswith(keep_suffix):
            f.unlink()

    git = ["git", "-C", str(repo)]
    run(*git, "checkout", "--orphan", "gh-pages-new")
    run(*git, "add", "-A")
    run(*git, "commit", "-q", "-m", f"Archive {month} to Google Drive")
    run(*git, "branch", "-M", "gh-pages")
    run(*git, "push", "-f", "origin", "gh-pages")
    run(*git, "reflog", "expire", "--expire=now", "--all")
    run(*git, "gc", "--prune=now", "--aggressive")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
