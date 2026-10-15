# UI components

This folder holds the source for the Gradio custom components used by the
Studio UI:

- `timeline/` builds `Timeline`, the section timeline with draggable keyframe
  markers.
- `motion_canvas/` builds `MotionCanvas`, the start-frame canvas for drawing
  motion arrows.

Each folder is a standard `gradio cc` project: `backend/` holds the Python
class, `frontend/` holds the Svelte source. The app never imports these
folders. It imports the built copies in `modules/ui/components/<name>/`,
which contain the Python class plus the compiled JavaScript in `templates/`.
Those built copies are committed, so running the app needs no Node toolchain.

## Rebuilding

After changing anything here, rebuild and re-vendor all components with:

    PYTHON=/path/to/venv/bin/python ui_components/build.sh

or a single one with `ui_components/build.sh timeline`. The venv must have
Gradio 5.25.x installed, and Node 18+ with npm must be on `PATH`.

For each component the script runs these steps, which you can also run by
hand inside the component folder:

    uv pip install -e .                  # gradio cc build needs the package installed
    (cd frontend && npm install)
    gradio cc build --no-generate-docs --python-path "$PYTHON" < /dev/null

It then copies `backend/<python package>/` to `modules/ui/components/<name>/`
(`gradio_timeline` becomes `timeline`, `gradio_motioncanvas` becomes
`motion_canvas`) and removes `.pyi`
files and caches. Commit the updated `templates/` folders along with the
source change. The script leaves the
editable package installed in the venv; you can uninstall it afterwards, since
the app uses the vendored copy.

## Caveat: no @gradio/atoms

Do not import anything from `@gradio/atoms` (such as `Block` or `BlockTitle`)
or from `@gradio/statustracker` in the Svelte files. With this toolchain those
imports are silently dropped from the bundle, and the page fails at runtime
with `Block is not defined`. The components use plain markup styled with
Gradio CSS variables instead. A type-only import from `@gradio/utils` is safe.

The same thing happens to imports in a `<script context="module">` block that
the block itself doesn't use: TypeScript drops them, even when the instance
script uses them. Keep imports in the script that uses them.
