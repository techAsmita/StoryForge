"""Template output for offline mode. Clearly marked so it is never mistaken for model output."""

BEATS = ["Inciting Incident", "Call to Action", "Rising Conflict", "Midpoint Turn", "Climax", "Resolution"]


def mock_response(step: str, ctx: dict) -> dict:
    hero = ctx.get("protagonist", "the hero")
    goal = ctx.get("goal", "find the truth")
    if step == "interview":
        return {"questions": [
            {"q": "What does the protagonist want most?", "a": f"[MOCK] To {goal.lower()}."},
            {"q": "What is at stake if they fail?", "a": "[MOCK] Their world collapses."},
            {"q": "What does the world rule cost them?", "a": "[MOCK] Every use takes something personal."},
            {"q": "Who opposes them?", "a": "[MOCK] A hooded rival who knows the truth."},
            {"q": "How is the twist foreshadowed?", "a": "[MOCK] Small echoes in chapters 1 and 3."},
        ]}
    if step == "branches":
        return {
            "branches": [
                {"id": "A", "premise": "[MOCK] A slow investigation.", "scores": {"originality": 5, "coherence": 8, "fit_to_brief": 6}},
                {"id": "B", "premise": "[MOCK] A race against time.", "scores": {"originality": 7, "coherence": 7, "fit_to_brief": 8}},
                {"id": "C", "premise": "[MOCK] A betrayal from within.", "scores": {"originality": 8, "coherence": 6, "fit_to_brief": 7}},
            ],
            "selected": "B",
            "reason": "[MOCK] Best balance of fit and coherence.",
        }
    out = {
        "title": "[MOCK] The Shattered Veil",
        "logline": f"[MOCK] {hero} sets out to {goal.lower()}. The deeper they go, the closer they come to a terrifying revelation.",
        "characters": [
            {"name": "Ren", "role": "protagonist", "visual_description": "black messy hair, glowing violet eye, long dark coat"},
            {"name": "Aiko", "role": "ally", "visual_description": "long silver hair, school uniform, calm eyes"},
            {"name": "Kaito", "role": "rival", "visual_description": "short dark hair, scar on cheek, black jacket"},
            {"name": "The Hooded One", "role": "villain", "visual_description": "hooded cloak, glowing sigil on chest"},
        ],
        "relationships": [
            {"source": "Ren", "target": "Aiko", "label": "ALLY"},
            {"source": "Ren", "target": "Kaito", "label": "CONFLICT"},
            {"source": "Ren", "target": "The Hooded One", "label": "LINKED DESTINY"},
        ],
        "beats": [{"name": b, "summary": f"[MOCK] {b} happens."} for b in BEATS],
        "chapters": [
            {"title": f"[MOCK] {t}", "text": (
                f"[MOCK] Demo text, not model output. Ren, {hero.lower()}, moves closer to the goal: {goal.lower()}. "
                "Aiko stays at his side while Kaito watches from the shadows, and the hooded figure leaves another sign. "
                "Add a Gemini API key in backend/.env to generate the real chapter."
            )} for t in ["The Fall", "The Sign", "The Price", "The Mirror", "The Choice"][: ctx.get("chapters", 4)]
        ],
        "scenes": [
            {"caption": "A city swallowed by darkness", "image_prompt": "lone figure facing a city collapsing into shadow"},
            {"caption": "The ally appears", "image_prompt": "girl with silver hair looking up in shock"},
            {"caption": "First battle", "image_prompt": "hero leaping through shattered glass, energy blade"},
            {"caption": "The hooded figure", "image_prompt": "hooded figure with glowing sigil in falling debris"},
        ],
    }
    if ctx.get("strategy") == "cot":
        out = {"plan": {"world": "[MOCK] world plan", "characters": "[MOCK] motivations", "arc": "[MOCK] arc"}, **out}
    return out
