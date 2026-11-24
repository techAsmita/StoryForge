"""Create submission/Code_XX.zip: source code, dependencies lists, data and art, without secrets or installed packages.

    python docs/package_code.py

Refuses to finish if anything that looks like an API key is found in the files being zipped.
"""
import json
import re
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INFO = json.loads((ROOT / "docs" / "project_info.json").read_text(encoding="utf-8"))
SKIP_DIRS = {".git", "node_modules", ".venv", "venv", "__pycache__", ".pytest_cache", "dist", "submission", "media", ".idea", ".vscode"}
SKIP_FILES = {".env", ".DS_Store"}
KEY_PATTERNS = [re.compile(p) for p in (r"AIza[0-9A-Za-z_\-]{30,}", r"sk-[A-Za-z0-9_\-]{20,}", r"sk_[A-Za-z0-9]{20,}", r"AQ\.[0-9A-Za-z_\-]{20,}")]
TEXT = {".py", ".js", ".jsx", ".mjs", ".json", ".md", ".txt", ".csv", ".html", ".css", ".example", ".toml", ".cfg", ".ini", ".sh", ""}


def files():
    for p in sorted(ROOT.rglob("*")):
        rel = p.relative_to(ROOT)
        if p.is_dir() or any(part in SKIP_DIRS for part in rel.parts) or p.name in SKIP_FILES:
            continue
        if p.name.startswith(".env") and p.name != ".env.example":
            continue
        yield p, rel


def main():
    out = ROOT / "submission" / f"Code_{INFO['group_no']}.zip"
    out.parent.mkdir(exist_ok=True)
    leaks = []
    items = list(files())
    for p, rel in items:
        if p.suffix in TEXT and p.stat().st_size < 5_000_000:
            text = p.read_text(encoding="utf-8", errors="ignore")
            if any(k.search(text) for k in KEY_PATTERNS):
                leaks.append(str(rel))
    if leaks:
        raise SystemExit("Possible API keys found, not packaging:\n  " + "\n  ".join(leaks))
    if not (ROOT / "data" / "experiments" / "summary.json").exists():
        print("Warning: data/experiments is empty. Run backend/scripts/experiments.py so the zip includes the results.")
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for p, rel in items:
            z.write(p, Path("StoryForge") / rel)
    mb = out.stat().st_size / 1e6
    print(f"Saved {out} ({len(items)} files, {mb:.1f} MB). No .env, keys, virtualenvs or node_modules included.")
    if mb > 100:
        print("Warning: larger than the 100 MB form limit.")


if __name__ == "__main__":
    main()
