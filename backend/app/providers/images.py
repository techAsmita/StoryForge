"""Image providers (syllabus: image generation + multimodal generation).

The LLM writes one visual prompt per scene plus a character sheet; this module turns those into
images and stores them under backend/media so they load instantly and survive rate limits.

openai        OpenAI image model (gpt-image-2 by default). Needs OPENAI_API_KEY; billed per image.
pollinations  Flux model via Pollinations. With POLLINATIONS_API_KEY -> gen.pollinations.ai (no
              rate limit on secret keys). Without a key -> anonymous endpoint, one image per ~45 s.
placeholder   offline gradient card with the caption (demos without internet)
"""
from __future__ import annotations

import base64
import time
from html import escape
from pathlib import Path
from urllib.parse import quote

import httpx

from ..config import get_settings


class ImageError(Exception):
    pass


def mood_for(tone: int) -> str:
    if tone < 34:
        return "moody twilight palette with violet highlights"
    if tone < 67:
        return "cinematic balanced palette"
    return "warm vibrant palette, soft golden light"


def build_image_prompt(scene_prompt: str, character_sheet: str, tone: int) -> str:
    # Repeating the same character sheet in every panel prompt keeps characters consistent.
    return (
        f"{scene_prompt}. Characters: {character_sheet}. "
        "Style: polished anime fantasy illustration, wide cinematic scene, characters shown at medium distance "
        f"within a detailed environment, soft dramatic lighting, {mood_for(tone)}, painterly, beautiful. "
        "No close-up faces, no gore, no text, no captions, no watermark."
    )


def fetch_image(prompt: str, width: int, height: int, seed: int) -> tuple[bytes, str]:
    """Call the configured image model and return (image bytes, file extension)."""
    s = get_settings()
    if s.image_provider == "openai":
        return _openai(prompt, width, height)
    return _pollinations(prompt, width, height, seed)


def _openai(prompt: str, width: int, height: int) -> tuple[bytes, str]:
    s = get_settings()
    if not s.openai_api_key:
        raise ImageError("IMAGE_PROVIDER=openai but OPENAI_API_KEY is empty in backend/.env")
    size = "1536x1024" if width > height * 1.2 else "1024x1536" if height > width * 1.2 else "1024x1024"
    try:
        r = httpx.post(
            "https://api.openai.com/v1/images/generations",
            headers={"Authorization": f"Bearer {s.openai_api_key}"},
            json={"model": s.openai_image_model, "prompt": prompt[:4000], "size": size,
                  "quality": s.openai_image_quality, "n": 1},
            timeout=180,
        )
    except httpx.HTTPError as exc:
        raise ImageError(f"OpenAI unreachable: {exc}") from exc
    if r.status_code == 429:
        raise ImageError("rate_limited")
    if r.status_code != 200:
        try:
            msg = r.json()["error"]["message"]
        except Exception:  # noqa: BLE001
            msg = r.text[:200]
        raise ImageError(f"OpenAI image error {r.status_code}: {msg}")
    item = r.json()["data"][0]
    if item.get("b64_json"):
        return base64.b64decode(item["b64_json"]), ".png"
    img = httpx.get(item["url"], timeout=120)
    return img.content, ".png"


def _pollinations(prompt: str, width: int, height: int, seed: int) -> tuple[bytes, str]:
    s = get_settings()
    params = {"width": width, "height": height, "seed": seed, "nologo": "true", "model": "flux"}
    headers = {}
    if s.pollinations_api_key:
        url = f"https://gen.pollinations.ai/image/{quote(prompt[:1500])}"
        headers["Authorization"] = f"Bearer {s.pollinations_api_key}"
    else:
        url = f"https://image.pollinations.ai/prompt/{quote(prompt[:1500])}"
    try:
        r = httpx.get(url, params=params, headers=headers, timeout=120, follow_redirects=True)
    except httpx.HTTPError as exc:
        raise ImageError(f"Image service unreachable: {exc}") from exc
    if r.status_code == 429:
        raise ImageError("rate_limited")
    if r.status_code != 200 or not r.headers.get("content-type", "").startswith("image/"):
        raise ImageError(f"Image service returned {r.status_code}")
    return r.content, ".png" if "png" in r.headers["content-type"] else ".jpg"


def render_to_file(prompt: str, seed: int, caption: str, dest: Path) -> Path:
    """Render one storyboard panel to dest (extension decided here). Returns the written path."""
    s = get_settings()
    dest.parent.mkdir(parents=True, exist_ok=True)
    if s.image_provider not in ("pollinations", "openai"):
        path = dest.with_suffix(".svg")
        path.write_text(_placeholder_svg(caption, seed), encoding="utf-8")
        return path
    data, ext = fetch_image(prompt, s.image_size, s.image_size, seed)
    path = dest.with_suffix(ext)
    path.write_bytes(data)
    return path


def min_interval() -> float:
    """Seconds to wait between images so free/low tiers are not rate limited."""
    s = get_settings()
    if s.image_provider == "openai":
        return 13.0  # entry-level OpenAI accounts allow about 5 images per minute
    if s.image_provider != "pollinations" or s.pollinations_api_key:
        return 0.0
    return s.image_min_interval


def sleep(seconds: float) -> None:  # separate so tests can patch it
    time.sleep(seconds)


def _placeholder_svg(caption: str, seed: int) -> str:
    hue = (seed * 47) % 360
    text = escape(caption[:60])
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="768" height="768" viewBox="0 0 768 768">'
        f'<defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1">'
        f'<stop offset="0" stop-color="hsl({hue},55%,28%)"/><stop offset="1" stop-color="#0d0a1f"/></linearGradient></defs>'
        f'<rect width="768" height="768" fill="url(#g)"/>'
        f'<circle cx="560" cy="200" r="90" fill="hsl({hue},60%,80%)" opacity=".25"/>'
        f'<text x="40" y="720" fill="#e9e2ff" font-family="sans-serif" font-size="30">{text}</text></svg>'
    )
