"""Generate StoryForge's interface artwork with the same image model the app uses (Flux via Pollinations).

Uses IMAGE_PROVIDER from backend/.env (openai or pollinations).
Run once from the backend folder (with the venv active):
    python scripts/generate_art.py            # skips images that already exist
    python scripts/generate_art.py --force    # regenerate everything
    python scripts/generate_art.py hero-create idea-neon-requiem   # only these

Images are saved to frontend/public/art/. Until an image exists, the app shows its built-in SVG scene.
Pollinations without a key: about one image every 45 s. OpenAI: about 13 s apart (entry-tier limit),
billed per image.
"""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app.config import get_settings  # noqa: E402
from app.providers import images  # noqa: E402

OUT = Path(__file__).resolve().parents[2] / "frontend" / "public" / "art"
STYLE = ("epic fantasy digital painting, rich purple and violet palette, glowing moonlight, cinematic lighting, "
         "highly detailed, atmospheric, no text, no watermark, no people in the foreground")

WIDE, CARD = (1600, 640), (1024, 640)
ASSETS = {
    # Page headers (the left side is dark so the title stays readable)
    "hero-create": (WIDE, "gothic castle with many glowing windows on a cliff, giant full moon behind it, starry purple night sky, "
                          "mist in the valley, empty dark sky on the left side of the image"),
    "hero-library": (WIDE, "giant ancient open book glowing with magical light, a fantasy castle and stars rising out of its pages, "
                           "swirling purple night sky, dark empty space on the left side of the image"),
    "hero-explore": (WIDE, "floating island with a crystal castle above purple clouds, distant moon, aurora, "
                           "dark empty sky on the left side of the image"),
    "hero-settings": (WIDE, "calm misty pine forest silhouettes at night, distant castle on a hill, stars and soft purple glow, "
                            "dark empty sky on the left side of the image"),
    "workspace-empty": (CARD, "moonlit gothic castle ruins on a hill, ravens, purple mist, mysterious and inviting"),
    # Explore starter ideas (match STARTER_IDEAS in frontend/src/lib/options.js)
    "idea-the-shattered-veil": (CARD, "shattered floating ruins around a moonlit gothic citadel, cracks of violet light in the sky"),
    "idea-neon-requiem": (CARD, "neon cyberpunk city on Mars at night, red dust, small robot on a rooftop looking at the stars"),
    "idea-the-cherry-blossom-cafe": (CARD, "cozy japanese café at dusk under cherry blossom trees, warm lanterns, petals falling"),
    "idea-the-last-lantern": (CARD, "old european town at night lit by glowing lanterns on winding streets, one lantern going out"),
    "idea-echoes-of-the-deep": (CARD, "drowned ancient city under the sea, shafts of moonlight through the water, glowing coral"),
    "idea-room-404": (CARD, "long empty vintage hotel corridor at night, one door glowing, eerie but not gory"),
    "idea-two-moons-apart": (CARD, "lighthouse on a cliff under two moons, letters floating on the wind, starry sky"),
    "idea-the-heist-of-hours": (CARD, "grand vault full of giant glowing clocks and hourglasses, golden gears, dramatic light"),
    "idea-the-dragons-apprentice": (CARD, "friendly giant dragon resting on a cliffside castle at sunset, a small apprentice with a lantern, warm magic light"),
    "idea-the-wizards-lost-socks": (CARD, "whimsical crooked wizard tower at night, enchanted socks flying around it, a smug black cat on the roof, playful glowing lights"),
}


def generate(name: str, size: tuple[int, int], prompt: str) -> None:
    data, _ = images.fetch_image(f"{prompt}. {STYLE}", size[0], size[1], seed=42)
    (OUT / f"{name}.jpg").write_bytes(data)  # browsers read PNG data fine whatever the extension


def main() -> None:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    force = "--force" in sys.argv
    provider = get_settings().image_provider
    if provider not in ("openai", "pollinations"):
        sys.exit(f"IMAGE_PROVIDER is '{provider}'. Set it to openai or pollinations in backend/.env first.")
    gap = images.min_interval()
    OUT.mkdir(parents=True, exist_ok=True)

    todo = [n for n in ASSETS if (not args or n in args) and (force or not (OUT / f"{n}.jpg").exists())]
    print(f"{len(todo)} image(s) to generate with {provider} into {OUT}" + (f" (~{int(gap)} s apart)" if gap else ""))
    for i, name in enumerate(todo, 1):
        size, prompt = ASSETS[name]
        for attempt in range(3):
            if (i > 1 or attempt > 0) and gap:
                time.sleep(gap)
            try:
                generate(name, size, prompt)
                print(f"[{i}/{len(todo)}] {name}.jpg saved")
                break
            except Exception as exc:  # noqa: BLE001  (report and retry)
                print(f"[{i}/{len(todo)}] {name}: {exc} (attempt {attempt + 1}/3)")
    print("Done. Refresh the browser to see the new artwork.")


if __name__ == "__main__":
    main()
