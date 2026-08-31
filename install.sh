#!/usr/bin/env bash
set -e
REPO="https://github.com/ensayiti/hermes-vacuum"
DEST="${HERMES_HOME:-$HOME/.hermes}/skills/productivity/hermes-vacuum"
TMP="/tmp/hermes-vacuum-install"

echo "Installing hermes-vacuum to $DEST"
rm -rf "$TMP"
if command -v git >/dev/null 2>&1; then
  echo "Cloning via git..."
  git clone --depth 1 "$REPO" "$TMP"
else
  echo "Downloading tarball..."
  mkdir -p "$TMP"
  curl -fsSL "$REPO/archive/refs/heads/main.tar.gz" | tar -xz -C "$TMP" --strip-components=1
fi
mkdir -p "$DEST"
cp -r "$TMP"/* "$DEST"/
rm -rf "$TMP"
echo "Installed. Verifying..."
hermes skills list | grep vacuum || true
echo ""
echo "Done. Restart hermes then run:"
echo "  hermes"
echo "  > /safe-cleanup dry-run"
