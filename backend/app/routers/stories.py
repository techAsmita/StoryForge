from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..config import get_settings
from ..db import get_db
from ..models import AppSetting, Story
from ..prompts.strategies import STRATEGIES
from ..providers import images
from ..providers.llm import ProviderError, get_llm
from ..schemas import GenerateRequest, StoryOut, StoryPatch, StorySummary, UserSettings
from ..services.image_worker import render_story_images
from ..services.story_service import generate_story

router = APIRouter(prefix="/api")


@router.get("/health")
def health():
    s = get_settings()
    live = s.effective_llm == "gemini"
    return {
        "status": "ok",
        "mode": "live" if live else "demo",
        "llm_provider": s.effective_llm,
        "model": s.gemini_model if live else "mock-template",
        "image_provider": s.image_provider,
        "image_model": s.openai_image_model if s.image_provider == "openai" else "flux",
        "image_key": bool(s.openai_api_key if s.image_provider == "openai" else s.pollinations_api_key),
        "image_interval_s": images.min_interval(),
    }


@router.get("/strategies")
def list_strategies():
    return [{"id": k, **v} for k, v in STRATEGIES.items()]


def _get(db: Session, story_id: int) -> Story:
    story = db.get(Story, story_id)
    if not story:
        raise HTTPException(404, "Story not found")
    return story


@router.post("/stories/generate", response_model=StoryOut)
def generate(req: GenerateRequest, background: BackgroundTasks, db: Session = Depends(get_db)):
    try:
        story = generate_story(db, get_llm(), req)
    except ProviderError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc
    background.add_task(render_story_images, story.id)
    return story


def _summary(s: Story) -> StorySummary:
    ready = [sc for sc in s.scenes if sc.status == "ready"]
    if len(ready) == len(s.scenes):
        status = "ready"
    elif any(sc.status in ("pending", "rendering") for sc in s.scenes):
        status = "rendering"
    else:
        status = "failed"
    return StorySummary(
        id=s.id, title=s.title, genre=s.genre, logline=s.output.get("logline", ""), strategy=s.strategy,
        provider=s.provider, temperature=s.sampling.get("temperature", 0), favorite=s.favorite,
        cover_url=ready[0].image_url if ready else "", scenes_total=len(s.scenes), scenes_ready=len(ready),
        image_status=status, created_at=s.created_at,
    )


@router.get("/stories", response_model=list[StorySummary])
def list_stories(db: Session = Depends(get_db)):
    return [_summary(s) for s in db.scalars(select(Story).order_by(Story.created_at.desc())).all()]


@router.get("/stories/{story_id}", response_model=StoryOut)
def get_story(story_id: int, db: Session = Depends(get_db)):
    return _get(db, story_id)


@router.patch("/stories/{story_id}", response_model=StoryOut)
def update_story(story_id: int, patch: StoryPatch, db: Session = Depends(get_db)):
    story = _get(db, story_id)
    if patch.favorite is not None:
        story.favorite = patch.favorite
    if patch.human_rating is not None:
        story.human_rating = patch.human_rating.model_dump()
    db.commit()
    db.refresh(story)
    return story


@router.post("/stories/{story_id}/images/retry", response_model=StoryOut)
def retry_images(story_id: int, background: BackgroundTasks, db: Session = Depends(get_db)):
    story = _get(db, story_id)
    for sc in story.scenes:
        if sc.status == "failed":
            sc.status, sc.error = "pending", ""
    db.commit()
    background.add_task(render_story_images, story.id)
    db.refresh(story)
    return story


@router.get("/stories/{story_id}/related", response_model=list[StoryOut])
def related(story_id: int, db: Session = Depends(get_db)):
    """All runs of the same idea + plot settings (for comparing strategies and sampling)."""
    story = _get(db, story_id)
    q = select(Story).where(Story.idea_key == story.idea_key).order_by(Story.created_at)
    return db.scalars(q).all()


@router.delete("/stories/{story_id}", status_code=204)
def delete_story(story_id: int, db: Session = Depends(get_db)):
    import shutil

    story = _get(db, story_id)
    db.delete(story)
    db.commit()
    shutil.rmtree(get_settings().media_dir / str(story_id), ignore_errors=True)


@router.get("/settings", response_model=UserSettings)
def get_user_settings(db: Session = Depends(get_db)):
    row = db.get(AppSetting, 1)
    return UserSettings(**(row.data if row else {}))


@router.put("/settings", response_model=UserSettings)
def save_user_settings(settings: UserSettings, db: Session = Depends(get_db)):
    row = db.get(AppSetting, 1) or AppSetting(id=1, data={})
    row.data = settings.model_dump()
    db.merge(row)
    db.commit()
    return settings
