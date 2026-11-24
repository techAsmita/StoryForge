"""Capture README screenshots of the running app on desktop, tablet and phone.

Start the backend and frontend first (http://localhost:5173), then:

    pip install playwright && python -m playwright install chromium     # one time
    python docs/take_screenshots.py

Saves docs/screenshots/<device>-<page>.png and docs/screenshots/responsive.png (a side-by-side collage).
The story page uses your most recent live (non-demo) story that has all four images.
"""
import json
import re
import sys
import urllib.request
from pathlib import Path

from PIL import Image, ImageDraw
from playwright.sync_api import sync_playwright

BASE = "http://localhost:5173"
OUT = Path(__file__).resolve().parent / "screenshots"
DEVICES = {
    "desktop": {"viewport": {"width": 1440, "height": 900}, "scale": 1.5},
    "tablet": {"viewport": {"width": 820, "height": 1180}, "scale": 2},
    "phone": {"viewport": {"width": 390, "height": 844}, "scale": 3},
}


def pick_story():
    try:
        stories = json.load(urllib.request.urlopen(f"{BASE}/api/stories", timeout=10))
    except Exception:
        sys.exit("App not reachable at http://localhost:5173. Start the backend and frontend first.")
    live = [s for s in stories if s["provider"] != "mock" and s["image_status"] == "ready"]
    if not live:
        sys.exit("No live story with all 4 images yet. Generate a story on Create (or press Retry images on one) "
                 "and wait until its 4 pictures appear, then run this again.")
    favs = [s for s in stories if s["favorite"]]
    if not favs:
        print("Tip: mark your illustrated stories as favourites; the Library screenshot then shows only those.")
    return live[0]["id"], bool(favs)


def shoot(page, url, path, tab=None, scroll=0):
    page.goto(url)
    page.wait_for_load_state("networkidle")
    if tab:
        page.get_by_role("button", name=re.compile(rf"^{re.escape(tab)}\b")).first.click()
        page.wait_for_timeout(600)
    if scroll:
        page.mouse.wheel(0, scroll)
    page.wait_for_timeout(1500)  # images and fonts
    page.screenshot(path=str(path))


def collage():
    d, t, p = (Image.open(OUT / f"{dev}-create.png") for dev in ("desktop", "tablet", "phone"))
    h = 900
    imgs = [im.resize((int(im.width * h / im.height), h)) for im in (d, t, p)]
    gap, pad = 40, 50
    canvas = Image.new("RGB", (sum(i.width for i in imgs) + gap * 2 + pad * 2, h + pad * 2), "#0b0919")
    x = pad
    draw = ImageDraw.Draw(canvas)
    for im in imgs:
        canvas.paste(im, (x, pad))
        draw.rounded_rectangle((x - 2, pad - 2, x + im.width + 2, pad + h + 2), radius=18, outline="#4C1D95", width=4)
        x += im.width + gap
    canvas.save(OUT / "responsive.png")


def main():
    OUT.mkdir(exist_ok=True)
    story, has_favs = pick_story()
    pages = {
        "create": ("/", None, 0),
        "story": (f"/library/{story}", None, 0),
        "story-scenes": (f"/library/{story}", "Scenes", 0),
        "story-promptlab": (f"/library/{story}", "Prompt Lab", 0),
        "story-evaluation": (f"/library/{story}", "Evaluation", 0),
        "library": ("/library", "Favorites" if has_favs else None, 0),
        "explore": ("/explore", None, 0),
        "settings": ("/settings", None, 0),
    }
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        for dev, cfg in DEVICES.items():
            ctx = browser.new_context(viewport=cfg["viewport"], device_scale_factor=cfg["scale"],
                                      is_mobile=dev == "phone", has_touch=dev != "desktop")
            page = ctx.new_page()
            for name, (url, tab, scroll) in pages.items():
                if dev != "desktop" and name in ("story-promptlab", "story-scenes", "settings"):
                    continue
                path = OUT / f"{dev}-{name}.png"
                shoot(page, BASE + url, path, tab, scroll)
                print("saved", path.relative_to(OUT.parent.parent))
            ctx.close()
        browser.close()
    collage()
    print("saved docs/screenshots/responsive.png")


if __name__ == "__main__":
    main()
