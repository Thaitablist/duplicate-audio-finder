#!/usr/bin/env bash
# Package the built .app into a distributable .dmg (macOS only).
# Prereq:  pyinstaller build/dupaudio.spec   (produces dist/Duplicate Audio Finder.app)
# Usage:   bash build/make_dmg.sh
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
APP="$ROOT/dist/Duplicate Audio Finder.app"
DMG="$ROOT/dist/DuplicateAudioFinder.dmg"
STAGING="$(mktemp -d)"
VOLNAME="Duplicate Audio Finder"

if [[ ! -d "$APP" ]]; then
  echo "error: $APP not found — run pyinstaller first." >&2
  exit 1
fi

# Stage the .app plus a symlink to /Applications for drag-to-install UX.
cp -R "$APP" "$STAGING/"
ln -s /Applications "$STAGING/Applications"

rm -f "$DMG"
hdiutil create \
  -volname "$VOLNAME" \
  -srcfolder "$STAGING" \
  -ov -format UDZO \
  "$DMG"

rm -rf "$STAGING"
echo "wrote $DMG"
