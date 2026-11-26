#!/usr/bin/env bash
set -euo pipefail

WIDGET_SRC="$(cd "$(dirname "$0")/ai-quotas.widget" && pwd)"
WIDGET_DST="$HOME/Library/Application Support/Übersicht/widgets/ai-quotas.widget"

mkdir -p "$WIDGET_DST"
cp "$WIDGET_SRC/index.jsx" "$WIDGET_DST/index.jsx"
cp "$WIDGET_SRC/fetch_quotas.py" "$WIDGET_DST/fetch_quotas.py"
chmod +x "$WIDGET_DST/fetch_quotas.py"

if [ ! -f "$WIDGET_DST/config.json" ]; then
  cp "$WIDGET_SRC/config.example.json" "$WIDGET_DST/config.json"
  chmod 600 "$WIDGET_DST/config.json"
  echo "Created $WIDGET_DST/config.json — please fill in your proxy / API keys."
else
  echo "Kept existing $WIDGET_DST/config.json."
fi

echo "Installed ai-quotas.widget to $WIDGET_DST"
