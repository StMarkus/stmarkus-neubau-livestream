# Livestream Capture and Periodic Upload

This folder contains scripts to capture the current livestream image and build a daily video for YouTube uploads.

## What it does

- `capture_image.py` downloads the image every 15 minutes (run via cron) and stores it locally with a timestamp.
- `build_hls.py` builds a weekly HLS playlist (current week by default) and can also build the full archive.
- `build_video.py` builds a weekly cumulative MP4 (current week by default) and can also build the full archive.
- `upload_youtube.py` uploads that MP4 to YouTube (OAuth required).

## Requirements

- Python 3.9+ (zoneinfo support)
- ffmpeg in PATH
- Python packages from `requirements.txt`

Check ffmpeg:

```sh
ffmpeg -version
```

Install Python packages:

```sh
python3 -m pip install -r requirements.txt
```

## Environment variables (optional)

- `IMAGE_URL` (required: camera image URL, not stored in the repo)
- `IMAGES_DIR` (default: ./images)
- `VIDEOS_DIR` (default: ./videos)
- `VIDEO_RANGE` (default: week)
- `VIDEO_OUTPUT` (default: week.mp4 or all.mp4)
- `TIMEZONE` (default: Europe/Berlin)
- `START_HOUR` (default: 6)
- `END_HOUR` (default: 20)
- `VIDEO_FPS` (default: 2)
- `HLS_DIR` (default: ./hls)
- `HLS_PLAYLIST` (default: stream.m3u8)
- `HLS_SEGMENT_TIME` (default: 4)
- `HLS_LIST_SIZE` (default: 0)
- `HLS_PLAYLIST_TYPE` (default: vod)
- `HLS_RANGE` (default: week)
- `YOUTUBE_CLIENT_SECRETS` (default: ./client_secrets.json)
- `YOUTUBE_TOKEN_FILE` (default: ./token.json)

## Cron setup (example)

Capture and rebuild HLS every 15 minutes between 06:00 and 20:00:

```sh
*/15 6-20 * * * cd /path/to/docroot && python3 capture_image.py && python3 build_hls.py --output-dir /path/to/docroot
```

Optional: build the weekly MP4 daily at 20:05 (and optionally the full archive):

```sh
5 20 * * * cd /path/to/neubau_livestream && python3 build_video.py --range week --output videos/week.mp4 && python3 upload_youtube.py --file videos/week.mp4 --title "Bauprojekt (Woche)"
# Optional full archive:
# 5 20 * * * cd /path/to/neubau_livestream && python3 build_video.py --range all --output videos/all.mp4
```

## HLS output

Place the HLS files in your Apache docroot:
`/path/to/docroot`
The playlist is `stream.m3u8` and segments are `segment_*.ts`.
URL: https://live-neubau.kopten.de/stream.m3u8

## Fotos auf GitHub Pages

Die Fotos liegen auf dem Branch `gh-pages` (GitHub Pages: Settings → Pages → Branch `gh-pages`, Ordner `/`).
`daily.html` lädt `images/image_YYYYMMDD_1400.jpg` relativ, z. B.
https://stmarkus.github.io/stmarkus-neubau-livestream/daily.html

### Einrichtung auf dem Server (einmalig)

```sh
# Deploy-Key mit Schreibrechten im Repo hinterlegen, dann:
git clone --branch gh-pages git@github.com:StMarkus/stmarkus-neubau-livestream.git pages
cd pages && chmod +x publish_images.sh archive_month.py
```

Der Branch `gh-pages` enthält `daily.html`, `publish_images.sh`, `archive_month.py` und `images/`
(initial z. B. mit `git checkout --orphan gh-pages` aus `main` erzeugen und die vorhandenen Fotos hinzufügen).
`capture_image.py` schreibt mit `IMAGES_DIR=/pfad/zu/pages/images` direkt dorthin.

### Cron

```sh
*/15 6-20 * * * cd /pfad/zu/neubau_livestream && IMAGE_URL=<Kamera-URL> IMAGES_DIR=/pfad/zu/pages/images python3 capture_image.py && /pfad/zu/pages/publish_images.sh
```

### Monatsarchiv in Google Drive

Einmalig `rclone config` (Remote `gdrive`, Typ Google Drive) auf dem Server ausführen.
Am 1. jedes Monats werden alle Fotos des Vormonats nach `gdrive:Neubau-Livestream/YYYY-MM/` kopiert,
per `rclone check` verifiziert, bis auf das 14:00-Foto aus `images/` entfernt und der Branch `gh-pages`
als einzelner Commit neu aufgebaut (Force-Push), damit das Repo klein bleibt:

```sh
30 21 1 * * cd /pfad/zu/pages && python3 archive_month.py
```

Test: `python3 archive_month.py --month 2026-02 --dry-run`. Ziel per `DRIVE_REMOTE` änderbar.
Ein Monat mit ~1.500 Fotos sind ca. 800 MB, das 1-GB-Limit von Pages reicht also genau einen Monat.

## OAuth for YouTube uploads (optional)

A stream key is only for live streaming, not for uploads. For uploads you need OAuth:

1. Create a Google Cloud project.
2. Enable YouTube Data API v3.
3. Create OAuth client credentials (Desktop app).
4. Download `client_secrets.json` into this folder.
5. Run once:

```sh
python3 upload_youtube.py --file videos/week.mp4
```

Follow the console prompt to authorize and create `token.json`.

## Notes

- The capture script skips if the timestamp file already exists.
- Daily video length is controlled by `VIDEO_FPS`.