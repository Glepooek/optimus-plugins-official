#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage: build-deb.sh --name <pkg> --version <ver> --arch <amd64|arm64> \
  --maintainer "<Name <email>>" --publish-dir <dir> --out-dir <dir> \
  [--desktop-file <path>] [--icon <path>] [--depends "<dep1, dep2>"] \
  [--description "<summary>"] [--executable <name>]

Packages an already-published Avalonia Linux build into a .deb via dpkg-deb.
Non-interactive: all inputs are flags, nothing is prompted.

Required:
  --name          Debian package name
  --version       Package version, e.g. 1.2.0
  --arch          amd64 | arm64
  --maintainer    "Name <email>"
  --publish-dir   Directory with the already-published executable and its files
  --out-dir       Directory to write the resulting .deb into

Optional:
  --executable    Executable filename inside --publish-dir (default: --name)
  --desktop-file  Path to a .desktop file to install under /usr/share/applications
  --icon          Path to an icon file to install under /usr/share/icons/hicolor/256x256/apps
  --depends       Comma-separated Depends field value (default: empty)
  --description   One-line Description summary (default: "<name> application")
  -h, --help      Show this help and exit

On success, prints the resulting .deb path to stdout and exits 0.
USAGE
}

PKG_NAME=""
PKG_VERSION=""
PKG_ARCH=""
MAINTAINER=""
PUBLISH_DIR=""
OUT_DIR=""
EXECUTABLE=""
DESKTOP_FILE=""
ICON_FILE=""
DEPENDS=""
DESCRIPTION=""

while [ $# -gt 0 ]; do
  case "$1" in
    --name) PKG_NAME="$2"; shift 2 ;;
    --version) PKG_VERSION="$2"; shift 2 ;;
    --arch) PKG_ARCH="$2"; shift 2 ;;
    --maintainer) MAINTAINER="$2"; shift 2 ;;
    --publish-dir) PUBLISH_DIR="$2"; shift 2 ;;
    --out-dir) OUT_DIR="$2"; shift 2 ;;
    --executable) EXECUTABLE="$2"; shift 2 ;;
    --desktop-file) DESKTOP_FILE="$2"; shift 2 ;;
    --icon) ICON_FILE="$2"; shift 2 ;;
    --depends) DEPENDS="$2"; shift 2 ;;
    --description) DESCRIPTION="$2"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown argument: $1" >&2; usage >&2; exit 2 ;;
  esac
done

for req in PKG_NAME PKG_VERSION PKG_ARCH MAINTAINER PUBLISH_DIR OUT_DIR; do
  if [ -z "${!req}" ]; then
    echo "Missing required flag for: $req" >&2
    usage >&2
    exit 2
  fi
done

case "$PKG_ARCH" in
  amd64|arm64) ;;
  *) echo "Invalid --arch: $PKG_ARCH (must be amd64 or arm64)" >&2; exit 2 ;;
esac

if [ ! -d "$PUBLISH_DIR" ] || [ -z "$(ls -A "$PUBLISH_DIR" 2>/dev/null)" ]; then
  echo "Publish directory does not exist or is empty: $PUBLISH_DIR" >&2
  exit 2
fi

if [ -z "$EXECUTABLE" ]; then
  EXECUTABLE="$PKG_NAME"
fi
if [ ! -f "$PUBLISH_DIR/$EXECUTABLE" ]; then
  echo "Executable not found in publish dir: $PUBLISH_DIR/$EXECUTABLE" >&2
  exit 2
fi

if [ -n "$DESKTOP_FILE" ] && [ ! -f "$DESKTOP_FILE" ]; then
  echo "Desktop file not found: $DESKTOP_FILE" >&2
  exit 2
fi
if [ -n "$ICON_FILE" ] && [ ! -f "$ICON_FILE" ]; then
  echo "Icon file not found: $ICON_FILE" >&2
  exit 2
fi

mkdir -p "$OUT_DIR"
if [ ! -w "$OUT_DIR" ]; then
  echo "Output directory is not writable: $OUT_DIR" >&2
  exit 2
fi

if [ -z "$DESCRIPTION" ]; then
  DESCRIPTION="$PKG_NAME application"
fi

STAGING="$(mktemp -d)"
trap 'rm -rf "$STAGING"' EXIT

mkdir -p \
  "$STAGING/DEBIAN" \
  "$STAGING/usr/bin" \
  "$STAGING/usr/lib/$PKG_NAME" \
  "$STAGING/usr/share/applications" \
  "$STAGING/usr/share/icons/hicolor/256x256/apps"

cp -r "$PUBLISH_DIR/." "$STAGING/usr/lib/$PKG_NAME/"
chmod +x "$STAGING/usr/lib/$PKG_NAME/$EXECUTABLE"

cat > "$STAGING/usr/bin/$PKG_NAME" <<EOF
#!/bin/sh
exec "/usr/lib/$PKG_NAME/$EXECUTABLE" "\$@"
EOF
chmod +x "$STAGING/usr/bin/$PKG_NAME"

if [ -n "$DESKTOP_FILE" ]; then
  cp "$DESKTOP_FILE" "$STAGING/usr/share/applications/$PKG_NAME.desktop"
fi

if [ -n "$ICON_FILE" ]; then
  cp "$ICON_FILE" "$STAGING/usr/share/icons/hicolor/256x256/apps/$PKG_NAME.${ICON_FILE##*.}"
fi

INSTALLED_SIZE="$(du -sk "$STAGING/usr" | cut -f1)"

cat > "$STAGING/DEBIAN/control" <<EOF
Package: $PKG_NAME
Version: $PKG_VERSION
Architecture: $PKG_ARCH
Installed-Size: $INSTALLED_SIZE
Maintainer: $MAINTAINER
Depends: $DEPENDS
Description: $DESCRIPTION
EOF

OUTPUT_DEB="$OUT_DIR/${PKG_NAME}_${PKG_VERSION}_${PKG_ARCH}.deb"
dpkg-deb --root-owner-group --build "$STAGING" "$OUTPUT_DEB" >&2

echo "$OUTPUT_DEB"
