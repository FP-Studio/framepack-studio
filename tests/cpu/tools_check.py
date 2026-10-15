"""
Browser check of the Tools tab against a running studio_fake.py.

Runs Process (filters + loop, a recipe, batch), Join clips and Edit frames
on small generated clips. Needs ffmpeg in modules/toolbox/bin (or let the
app's one-time setup fetch it). Not a pytest test; run it by hand:

    python tests/cpu/tools_check.py --url http://127.0.0.1:7861/
"""

import argparse
import os
import subprocess
import sys
import tempfile
import time

from playwright.sync_api import sync_playwright

parser = argparse.ArgumentParser()
parser.add_argument("--url", default="http://127.0.0.1:7861/")
parser.add_argument("--ffmpeg", default="ffmpeg")
args = parser.parse_args()

results = []


def check(name, ok, detail=""):
    results.append(bool(ok))
    print(
        ("PASS " if ok else "FAIL ") + name + (f" — {detail}" if detail else ""),
        flush=True,
    )


def make_clip(path, hue):
    subprocess.run(
        [
            args.ffmpeg,
            "-y",
            "-loglevel",
            "error",
            "-f",
            "lavfi",
            "-i",
            f"testsrc=size=160x96:rate=10:duration=1,hue=h={hue}",
            "-pix_fmt",
            "yuv420p",
            path,
        ],
        check=True,
    )


def result_src(pg):
    return pg.evaluate("() => document.querySelector('#tools-result video')?.src || ''")


def wait_result(pg, before, timeout=120):
    t0 = time.time()
    while time.time() - t0 < timeout:
        src = result_src(pg)
        if src and src != before:
            return src
        time.sleep(1)
    return ""


def frame_count(pg):
    """Distinct frames in the gallery (preview mode repeats thumbnails)."""
    return pg.evaluate(
        """() => new Set([...document.querySelectorAll(
            '#toolbox_frames_gallery img')].map(i => i.src)).size"""
    )


def mode(pg, name):
    pg.locator("#tools-mode label", has_text=name).click()
    time.sleep(1.2)


def switch(pg, key):
    pg.locator(f"#step-{key} .step-switch input").click()
    time.sleep(0.8)


tmp = tempfile.mkdtemp()
clips = [os.path.join(tmp, f"clip{i}.mp4") for i in range(2)]
for i, c in enumerate(clips):
    make_clip(c, i * 120)

with sync_playwright() as p:
    browser = p.chromium.launch()
    pg = browser.new_page(viewport={"width": 1440, "height": 900})
    errors = []
    pg.on("pageerror", lambda e: errors.append(str(e)[:200]))
    pg.goto(args.url)
    pg.wait_for_selector("button[role=tab]")
    time.sleep(4)
    pg.get_by_role("tab", name="Tools", exact=True).click()
    time.sleep(1.5)
    run = pg.locator("#toolbox-start-pipeline-btn")
    summary = pg.locator("#tools-run .prose.run-summary")

    # Process
    check("Run waits for a video", not run.is_enabled())
    pg.locator("#toolbox-video-player input[type=file]").set_input_files(clips[0])
    time.sleep(3)
    check("Run waits for a step", "at least one step" in summary.inner_text())
    switch(pg, "filters")
    switch(pg, "loop")
    check(
        "the summary lists the steps in run order",
        "Filters → Loop · 1 video" in summary.inner_text(),
        summary.inner_text(),
    )
    check(
        "only switched-on steps show settings",
        pg.locator("#step-loop .step-body").is_visible()
        and not pg.locator("#step-upscale .step-body").is_visible(),
    )
    check(
        "the input's details fill in on upload",
        "160" in pg.locator(".analysis-box textarea").input_value(),
    )
    before = result_src(pg)
    run.click()
    check("filters + loop produce a result", bool(wait_result(pg, before)))

    # Recipe: save, reset by loading "No recipe", load it back, delete
    recipe = pg.locator("#recipe-select input")
    recipe.fill("Check recipe")
    recipe.press("Enter")
    pg.locator("button", has_text="Save recipe").click()
    time.sleep(1.5)
    switch(pg, "loop")  # turn one off so loading has something to restore
    recipe.click()
    pg.get_by_role("option", name="No recipe").click()
    time.sleep(1.5)
    check(
        "No recipe turns every step off",
        not pg.locator("#step-filters .step-switch input").is_checked(),
    )
    recipe.click()
    pg.get_by_role("option", name="Check recipe").click()
    time.sleep(1.5)
    check(
        "loading the recipe turns its steps back on",
        pg.locator("#step-filters .step-switch input").is_checked()
        and pg.locator("#step-loop .step-switch input").is_checked(),
    )
    pg.locator("#tools-main button", has_text="Delete").first.click()
    time.sleep(0.8)
    pg.locator(".inline-form:visible button", has_text="Delete").first.click()
    time.sleep(1.5)
    check(
        "the recipe deletes", recipe.input_value() == "No recipe", recipe.input_value()
    )

    # Batch
    switch(pg, "filters")
    pg.locator("button", has_text="Batch: process several videos").click()
    time.sleep(0.8)
    pg.locator("#tools-main input[type=file][multiple]").first.set_input_files(clips)
    time.sleep(3)
    check(
        "batch files take over the run",
        "2 videos" in summary.inner_text() and "Run on 2 videos" in run.inner_text(),
        summary.inner_text(),
    )
    before = result_src(pg)
    run.click()
    check("the batch runs", bool(wait_result(pg, before)))

    # Join
    mode(pg, "Join clips")
    check(
        "Join hides the single input",
        not pg.locator("#toolbox-video-player").is_visible(),
    )
    pg.locator("#tools-main input[type=file][multiple]").nth(1).set_input_files(clips)
    time.sleep(2)
    before = result_src(pg)
    pg.locator("#tools-main button", has_text="Join").last.click()
    check("two clips join", bool(wait_result(pg, before)))

    # Edit frames
    mode(pg, "Edit frames")
    pg.locator("button", has_text="Extract").click()
    t0 = time.time()
    while (
        time.time() - t0 < 60 and not pg.locator("#toolbox_frames_gallery img").count()
    ):
        time.sleep(1)
    frames = frame_count(pg)
    check("extracting opens the frames", frames > 1, f"{frames} frames")
    pg.locator("#toolbox_frames_gallery img").first.click()
    time.sleep(1)
    pg.locator("button", has_text="Delete frame").click()
    time.sleep(2)
    after = frame_count(pg)
    check("a frame deletes", after == frames - 1, f"{frames} → {after}")
    before = result_src(pg)
    pg.locator("button", has_text="Rebuild").click()
    check("the frames rebuild into a video", bool(wait_result(pg, before)))
    pg.locator("button", has_text="Delete folder").click()
    time.sleep(0.8)
    pg.locator(".inline-form:visible button", has_text="Delete").click()
    time.sleep(2)
    check(
        "the folder deletes",
        pg.locator("#toolbox_frames_gallery img").count() == 0,
    )

    check("no page errors", not errors, "; ".join(errors[:3]))
    browser.close()

print(f"\n{sum(results)}/{len(results)} passed")
sys.exit(0 if all(results) else 1)
