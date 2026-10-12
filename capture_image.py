#!/usr/bin/env python3
import datetime as dt
import os
from pathlib import Path
import sys
from zoneinfo import ZoneInfo

import requests


def env(name: str, default: str) -> str:
    return os.getenv(name, default)


def require_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        sys.exit(f"{name} is not set (camera image URL)")
    return value


def in_time_window(now: dt.datetime, start_hour: int, end_hour: int) -> bool:
    if now.hour < start_hour:
        return False
    if now.hour > end_hour:
        return False
    if now.hour == end_hour and now.minute > 0:
        return False
    return True


def main() -> int:
    url = require_env("IMAGE_URL")
    images_dir = Path(env("IMAGES_DIR", "./images"))
    tz_name = env("TIMEZONE", "Europe/Berlin")
    start_hour = int(env("START_HOUR", "6"))
    end_hour = int(env("END_HOUR", "20"))
    timeout = int(env("HTTP_TIMEOUT", "20"))

    now = dt.datetime.now(ZoneInfo(tz_name))
    if not in_time_window(now, start_hour, end_hour):
        return 0

    images_dir.mkdir(parents=True, exist_ok=True)
    # Auf Viertelstunde abrunden, weil geplante Läufe verspätet starten können
    slot = now.replace(minute=now.minute // 15 * 15, second=0, microsecond=0)
    stamp = slot.strftime("%Y%m%d_%H%M")
    filename = f"image_{stamp}.jpg"
    target = images_dir / filename

    if target.exists():
        return 0

    tmp_path = target.with_suffix(".tmp")
    try:
        response = requests.get(url, timeout=timeout)
        response.raise_for_status()
        with tmp_path.open("wb") as handle:
            handle.write(response.content)
        tmp_path.replace(target)
    except Exception as exc:
        if tmp_path.exists():
            tmp_path.unlink(missing_ok=True)
        print(f"Download failed: {exc}", file=sys.stderr)
        return 2

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
