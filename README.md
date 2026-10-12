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

Die Fotos liegen auf dem Branch `gh-pages` (Settings → Pages → Branch `gh-pages`, Ordner `/`).
`daily.html` lädt `images/image_YYYYMMDD_1400.jpg` relativ und fällt bei fehlendem Foto bis zu 7 Tage zurück:
https://stmarkus.github.io/stmarkus-neubau-livestream/daily.html

Alles läuft in GitHub Actions, es ist kein Server nötig. `daily.html` und `archive_month.py` liegen für Pages
zusätzlich auf `gh-pages` und müssen dort bei Änderungen mitgezogen werden.

### Secrets und Variablen (Settings → Secrets and variables → Actions)

- Secret `IMAGE_URL`: URL des Kamerabildes
- Secret `RCLONE_CONFIG`: kompletter Inhalt einer `rclone.conf` mit einem Remote `gdrive` (Google Drive)
- Variable `DRIVE_REMOTE` (optional): Ziel, default `gdrive:Neubau-Livestream`

### Workflows

- `capture.yml`: alle 15 Minuten (06:00-20:00 Berlin) Kamerabild holen und nach `gh-pages` committen.
  GitHub führt Schedules teils verspätet aus.
- `archive.yml`: am 1. jedes Monats alle Fotos des Vormonats nach `gdrive:Neubau-Livestream/YYYY-MM/` kopieren,
  per `rclone check` verifizieren, bis auf das 14:00-Foto aus `images/` entfernen und `gh-pages` als einzelnen
  Commit neu aufbauen (Force-Push), damit das Repo klein bleibt. Manuell für einen beliebigen Monat startbar
  (Actions → Archive month to Google Drive → Run workflow, z. B. `2026-02`).

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