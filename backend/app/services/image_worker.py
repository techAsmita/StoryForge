"""Background job: render a story's storyboard panels one by one and save them to disk."""
import logging

from ..config import get_settings
from ..db import SessionLocal
from ..models import Scene, Story
from ..providers import images

log = logging.getLogger("storyforge.images")
MAX_ATTEMPTS = 3


def render_story_images(story_id: int) -> None:
    s = get_settings()
    db = SessionLocal()
    try:
        story = db.get(Story, story_id)
        if not story:
            return
        first = True
        for scene in story.scenes:
            if scene.status == "ready":
                continue
            _render_scene(db, scene, story, s.media_dir, wait_first=not first)
            first = False
    finally:
        db.close()


def _render_scene(db, scene: Scene, story: Story, media_dir, wait_first: bool) -> None:
    gap = images.min_interval()
    scene.status, scene.error = "rendering", ""
    db.commit()
    seed = (story.sampling.get("seed") or 7) + scene.index
    for attempt in range(1, MAX_ATTEMPTS + 1):
        if gap and (wait_first or attempt > 1):
            images.sleep(gap)
        try:
            path = images.render_to_file(
                scene.image_prompt, seed, scene.caption, media_dir / str(story.id) / f"scene-{scene.index}"
            )
            scene.image_url = f"/media/{story.id}/{path.name}"
            scene.status, scene.error = "ready", ""
            db.commit()
            return
        except images.ImageError as exc:
            log.warning("story %s scene %s attempt %s failed: %s", story.id, scene.index, attempt, exc)
            scene.error = "Image service rate limit reached." if str(exc) == "rate_limited" else str(exc)
            wait_first = True
    scene.status = "failed"
    db.commit()
