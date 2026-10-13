#!/usr/bin/env bash
# Build the FramePack Studio Gradio custom components and vendor the output
# into modules/ui/components/<name>/.
#
# usage: ui_components/build.sh [timeline|motion_canvas ...]   (default: all)
#        PYTHON=/path/to/venv/bin/python ui_components/build.sh
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC_ROOT="${SRC_ROOT:-$HERE}"
DEST_ROOT="${DEST_ROOT:-$HERE/../modules/ui/components}"
PYTHON="$(command -v "${PYTHON:-python}")"
BIN="$(dirname "$PYTHON")"

# source dir : python package built by `gradio cc build` : vendored name
COMPONENTS=(
  "timeline:gradio_timeline:timeline"
  "motion_canvas:gradio_motioncanvas:motion_canvas"
)

if command -v uv >/dev/null 2>&1; then
  pip_install() { VIRTUAL_ENV="$(dirname "$BIN")" uv pip install --python "$PYTHON" "$@"; }
else
  pip_install() { "$PYTHON" -m pip install "$@"; }
fi

mkdir -p "$DEST_ROOT"
[ -f "$DEST_ROOT/__init__.py" ] || echo '"""Custom Gradio components (built from ui_components/)."""' > "$DEST_ROOT/__init__.py"

for spec in "${COMPONENTS[@]}"; do
  IFS=: read -r src pkg name <<< "$spec"
  if [ $# -gt 0 ] && [[ " $* " != *" $src "* ]]; then continue; fi
  echo "==> $src"
  cd "$SRC_ROOT/$src"
  pip_install -e . >/dev/null
  (cd frontend && npm install --no-audit --no-fund >/dev/null)
  PATH="$BIN:$PATH" "$BIN/gradio" cc build --no-generate-docs --python-path "$PYTHON" < /dev/null
  rm -rf "${DEST_ROOT:?}/$name"
  mkdir -p "$DEST_ROOT/$name"
  cp -R "backend/$pkg/." "$DEST_ROOT/$name/"
  find "$DEST_ROOT/$name" \( -name '__pycache__' -o -name '*.pyi' -o -name '*.pyc' \) -prune -exec rm -rf {} +
  rm -rf dist
  echo "    -> $DEST_ROOT/$name"
done
