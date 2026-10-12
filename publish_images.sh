#!/bin/sh
# Committet und pusht neue Fotos auf den gh-pages-Branch (GitHub Pages).
# Aufruf per Cron direkt nach capture_image.py, im Klon des gh-pages-Branches.
set -eu
cd "$(dirname "$0")"

exec 9>.publish.lock
flock -n 9 || exit 0

git add images
git diff --cached --quiet && exit 0
git commit -q -m "Add images $(date +%Y%m%d_%H%M)"
git push -q origin gh-pages
