#!/usr/bin/env bash
# Installs the Python packages the reel pipeline needs and checks the system tools.
set -u
pip install -q edge-tts faster-whisper numpy scipy yt-dlp certifi 2>&1 | tail -1
ok=1
for t in ffmpeg ffprobe node; do
  command -v "$t" >/dev/null || { echo "missing: $t"; ok=0; }
done
if ! NODE_PATH="${NODE_PATH:-/opt/node22/lib/node_modules}" node -e "require('playwright')" 2>/dev/null; then
  echo "missing: playwright for node (npm i -g playwright, then npx playwright install chromium)"; ok=0
fi
[ "$ok" = 1 ] && echo "meme-reel: ready"
