"""
Browser check of the UI against a running studio_fake.py.

Drives the real page like a user: capability gating, start frame, arrows,
keyframes, a job through to the Library, re-roll from a section, a video
extension and presets. Not a pytest test; run it by hand:

    python tests/cpu/ui_check.py --url http://127.0.0.1:7861/ --outputs outputs

See tests/cpu/README.md for the extra setup (Playwright, ffprobe, decord).
"""

import argparse
import glob
import os
import sys
import tempfile
import time

import numpy as np
from PIL import Image
from playwright.sync_api import sync_playwright

parser = argparse.ArgumentParser()
parser.add_argument("--url", default="http://127.0.0.1:7861/")
parser.add_argument("--outputs", default="outputs", help="the app's output folder")
parser.add_argument(
    "--no-video",
    action="store_true",
    help="skip the video extension (needs real decord)",
)
args = parser.parse_args()

results = []


def check(name, ok, detail=""):
    results.append(bool(ok))
    print(
        ("PASS " if ok else "FAIL ") + name + (f" — {detail}" if detail else ""),
        flush=True,
    )


def block(pg, label):
    return pg.locator(".block:visible", has=pg.get_by_text(label, exact=True)).first


def set_number(pg, label, value):
    inp = block(pg, label).locator("input[type=number]").first
    inp.fill(str(value))
    inp.press("Enter")
    time.sleep(0.6)


def radio(pg, value):
    pg.locator(f"label[data-testid='{value}-radio-label']").first.click()
    time.sleep(1.2)


def visible_checks(pg):
    """Rail messages the user can actually see (opacity and size included)."""
    return pg.evaluate(
        """() => [...document.querySelectorAll('.prose.checks .fps-check')]
            .filter(e => getComputedStyle(e).opacity !== '0'
                && e.closest('.block').getBoundingClientRect().height > 10)
            .map(e => e.innerText).join(' ')"""
    )


def videos():
    return set(glob.glob(os.path.join(args.outputs, "*.mp4")))


def wait_idle_with_new(pg, before, timeout=240):
    t0 = time.time()
    while time.time() - t0 < timeout:
        new = videos() - before
        pill = pg.locator(".status-pill").inner_text()
        if new and "Running" not in pill and "waiting" not in pill:
            return new
        time.sleep(2)
    return set()


tmp = tempfile.mkdtemp()
image_path = os.path.join(tmp, "start.png")
gradient = np.zeros((256, 256, 3), np.uint8)
gradient[..., 0] = np.linspace(40, 220, 256)[None, :]
gradient[..., 2] = np.linspace(200, 60, 256)[:, None]
Image.fromarray(gradient).save(image_path)

with sync_playwright() as p:
    browser = p.chromium.launch()
    pg = browser.new_page(viewport={"width": 1440, "height": 900})
    errors = []
    pg.on("pageerror", lambda e: errors.append(str(e)[:200]))
    pg.goto(args.url)
    pg.wait_for_selector("button[role=tab]")
    time.sleep(6)
    add = pg.locator("#add-to-queue")

    # Capability gating
    radio(pg, "F1")
    pg.get_by_role("tab", name="Keyframes", exact=True).click()
    time.sleep(0.8)
    reason = pg.locator(".field-note.warn").filter(
        has_text="Keyframes only works with Original"
    )
    check("F1 explains why keyframes are off", reason.count() >= 1)
    radio(pg, "Video")
    check(
        "Video without a video blocks the queue",
        not add.is_enabled() and "Add a video" in visible_checks(pg),
    )
    radio(pg, "Original")
    radio(pg, "Image")
    check("Original from an image can queue", add.is_enabled())

    # Start frame, arrow, keyframe
    block(pg, "Start frame · optional").locator("input[type=file]").set_input_files(
        image_path
    )
    time.sleep(3)
    pg.get_by_role("tab", name="Camera & arrows", exact=True).click()
    time.sleep(1)
    box = pg.locator(".motion-group .stage").first.bounding_box()
    pg.mouse.move(box["x"] + box["width"] * 0.3, box["y"] + box["height"] * 0.5)
    pg.mouse.down()
    pg.mouse.move(
        box["x"] + box["width"] * 0.6, box["y"] + box["height"] * 0.4, steps=8
    )
    pg.mouse.up()
    time.sleep(2)
    check(
        "a drawn arrow shows on the timeline",
        "1 arrow" in pg.locator("#create-timeline").inner_text(),
    )
    pg.get_by_role("tab", name="Keyframes", exact=True).click()
    time.sleep(0.8)
    block(pg, "Keyframe 1").locator("input[type=file]").set_input_files(image_path)
    time.sleep(3)
    check(
        "a keyframe shows on the timeline",
        "K1" in pg.locator("#create-timeline").inner_text(),
    )
    radio(pg, "F1")
    check(
        "F1 warns the keyframe will be skipped",
        "Keyframes will be skipped" in visible_checks(pg),
    )
    radio(pg, "Original")
    # Clear the keyframe so the job below is a plain three-section job
    clear = block(pg, "Keyframe 1").locator(
        "button[aria-label='Clear'], button[aria-label='Remove Image']"
    )
    if clear.count():
        clear.first.click()
        time.sleep(1)

    # A short three-section job
    set_number(pg, "Length (seconds)", 3.6)
    set_number(pg, "Width", 128)
    set_number(pg, "Height", 128)
    pg.locator("button", has_text="Quality & speed").first.click()
    time.sleep(0.5)
    set_number(pg, "Steps", 2)
    before = videos()
    add.click()
    new = wait_idle_with_new(pg, before)
    check("the job finishes", bool(new))
    rail_src = pg.evaluate(
        "() => [...document.querySelectorAll('#create-rail video')].map(v => v.src).join(' ')"
    )
    check("the result plays in the rail", ".mp4" in rail_src)
    clip = sorted(new, key=os.path.getmtime)[-1] if new else None

    # Library, use these settings, re-roll from section 2
    pg.get_by_role("tab", name="Library", exact=True).click()
    time.sleep(3)
    pg.locator("#library-gallery img").first.click()
    time.sleep(3)
    check(
        "the Library shows the job's settings", pg.locator(".lib-summary").count() == 1
    )
    pg.locator("button", has_text="Re-roll from a section").first.click()
    time.sleep(1.5)
    cells = pg.locator("#library-detail .track.sections .cell")
    labels = [cells.nth(i).inner_text().strip() for i in range(cells.count())]
    check(
        "sections read 3, 2, 1 in time order (Original runs backwards)",
        labels == ["3", "2", "1"],
        str(labels),
    )
    if "2" in labels:
        cells.nth(labels.index("2")).click()
        time.sleep(1.5)
        pg.locator("button", has_text="Re-roll from section 2").first.click()
        time.sleep(4)
        check(
            "Create shows the re-roll", pg.locator(".reroll-banner").first.is_visible()
        )
        before = videos()
        add.click()
        check("the re-roll finishes", bool(wait_idle_with_new(pg, before)))
        pg.locator(".reroll-banner button").first.click()
        time.sleep(1)

    # Video extension
    if not args.no_video and clip:
        radio(pg, "Video")
        block(pg, "Video to extend").locator("input[type=file]").set_input_files(clip)
        time.sleep(4)
        check("a video unblocks the queue", add.is_enabled())
        before = videos()
        add.click()
        new = wait_idle_with_new(pg, before)
        check(
            "the video extension finishes with a combined video",
            any("combined" in n for n in new),
        )
        radio(pg, "Image")

    # Presets
    preset_box = pg.locator(".preset-col input").first
    preset_box.fill("UI check")
    preset_box.press("Enter")
    time.sleep(1)
    pg.locator("button", has_text="Save preset").first.click()
    time.sleep(2)
    check(
        "a preset saves and is selected",
        pg.locator(".preset-col input").first.input_value() == "UI check",
    )
    pg.locator("button", has_text="Delete preset").first.click()
    time.sleep(1)
    pg.locator(".inline-form button", has_text="Delete").first.click()
    time.sleep(2)

    check("no page errors", not errors, "; ".join(errors[:3]))
    browser.close()

print(f"\n{sum(results)}/{len(results)} passed")
sys.exit(0 if all(results) else 1)
