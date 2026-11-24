# PROJECT_STATUS

Read this first in any new Claude conversation to resume without re-explaining the project.

## Goal
UCS748 Generative AI project, target 17–20/20. Working end to end, covering every syllabus element, fully explainable in the viva. No unnecessary features.

## Stack
React + Vite + Tailwind v4 + React Router · FastAPI · PostgreSQL (SQLAlchemy 2) · Gemini API (free tier, auto-enabled when the key is set) · Pollinations Flux images rendered server-side · demo mode for offline work.

## Done
- v0.1 (2026-11-10): backend, 4 prompting strategies, Gemini/mock providers, first studio UI.
- v0.2 (2026-11-10): 4-page redesign (Create, Library, Explore, Settings) in sentence case; story workspace with Story / Scenes / Prompt Lab / Evaluation; server-side image worker with rate-limit spacing, retries and Retry button; automatic metrics + human ratings; strategy comparison and temperature sweep experiments; favorites, search, sort; settings saved in PostgreSQL; auto live/demo switch; idempotent column upgrades on startup; 8 backend tests.

- v0.3 (2026-11-10): painted interface art via scripts/generate_art.py (Flux), full-bleed page headers, Plus Jakarta Sans headings + heavier serif titles, chapter-title cleanup, default model gemini-3.5-flash-lite (2.5 retired for new users), clearer backend error messages.
- v0.4 (2026-11-10): optional OpenAI image provider (gpt-image-2, IMAGE_PROVIDER=openai; text stays Gemini for Top-K); softer anime panel style (wide scenes, no close-up faces); shorter/lighter page headers; hidden chip scrollbars; 2 new starter ideas (Fantasy, Comedy); slimmer settings save bar; 10 backend tests.
- v0.5 (2026-11-24): submission pipeline: experiments runner + data export (data/), report builder (Report_09.pdf), slide builder (PPT_09.pptx, 10 slides), code packager with key-leak guard (Code_09.zip), one-command docs/build_all.sh.

## Next
1. Run `bash docs/build_all.sh` in live mode, check the PDF and PPT, upload the three files.
2. Create the GitHub repo (name must match github_url in docs/project_info.json).
3. Optional depth: semantic similarity via Gemini embeddings; a small LoRA fine-tune on Colab compared against Gemini (only claim it if done).
4. Report, PPT, demo video script, GAN vs diffusion section.

## Known limits
- Free Gemini quotas are small; experiments use 1–3 calls per run.
- Anonymous Pollinations is slow (~45 s per image); a free sk_ key fixes it.
- Image jobs interrupted by a server restart are marked failed; use Retry images.
