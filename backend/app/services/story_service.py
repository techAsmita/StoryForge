"""Runs a prompting strategy end to end and saves everything needed to reproduce and compare it."""
import hashlib
import json

from sqlalchemy.orm import Session

from ..models import GenerationRun, Scene, Story
from ..prompts import strategies as S
from ..providers.images import build_image_prompt
from ..providers.llm import LLMProvider, ProviderError, parse_json
from ..schemas import GenerateRequest
from .evaluation import evaluate

REQUIRED_KEYS = ("title", "logline", "characters", "beats", "chapters", "scenes")


def idea_key(req: GenerateRequest) -> str:
    """Identical idea + plot dials => identical key, so different strategies/sampling can be compared."""
    payload = json.dumps({"idea": req.idea.model_dump(), "plot": req.plot.model_dump()}, sort_keys=True)
    return hashlib.sha256(payload.encode()).hexdigest()[:16]


def generate_story(db: Session, llm: LLMProvider, req: GenerateRequest) -> Story:
    story_brief = S.brief(req.idea, req.plot)
    context = {**req.idea.model_dump(), "strategy": req.strategy, "chapters": S.length_targets(req.plot.length)[0]}
    artifacts: dict = {}
    runs: list[GenerationRun] = []
    output: dict = {}

    for step in S.STRATEGIES[req.strategy]["steps"]:
        if step == "interview":
            prompt = S.interview_prompt(story_brief)
        elif step == "branches":
            prompt = S.branches_prompt(story_brief)
        else:
            prompt = S.write_prompt(req.strategy, story_brief, artifacts)

        completion = llm.complete(step, S.SYSTEM, prompt, req.sampling, context)
        data = parse_json(completion.text)
        runs.append(GenerationRun(
            step=step, prompt=prompt, params=req.sampling.model_dump(),
            raw_output=completion.text, latency_ms=round(completion.latency_ms, 1),
        ))
        if step == "write":
            output = data
        else:
            artifacts[step] = data

    missing = [k for k in REQUIRED_KEYS if k not in output]
    if missing:
        raise ProviderError(f"The model's answer is missing: {', '.join(missing)}. Please try again.")
    if "plan" in output:
        artifacts["plan"] = output.pop("plan")

    story = Story(
        title=output["title"], genre=req.idea.genre, strategy=req.strategy,
        provider=llm.name, model=llm.model,
        idea=req.idea.model_dump(), plot=req.plot.model_dump(), sampling=req.sampling.model_dump(),
        output=output, artifacts=artifacts, runs=runs, idea_key=idea_key(req),
    )

    # Multimodal step: LLM-written scene prompts + one shared character sheet -> image model.
    sheet = "; ".join(f"{c['name']}: {c.get('visual_description', '')}" for c in output["characters"])
    for i, sc in enumerate(output["scenes"][:4], start=1):
        story.scenes.append(Scene(
            index=i, caption=sc["caption"], status="pending",
            image_prompt=build_image_prompt(sc["image_prompt"], sheet, req.plot.tone),
        ))

    story.metrics = evaluate(story)
    db.add(story)
    db.commit()
    db.refresh(story)
    return story
