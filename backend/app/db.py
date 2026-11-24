from sqlalchemy import create_engine, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from .config import get_settings

engine = create_engine(get_settings().database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Columns added after the first release. create_all() only creates missing TABLES, so existing
# databases get the new columns here. (Small, idempotent; a full Alembic setup would be overkill.)
UPGRADES = [
    "ALTER TABLE stories ADD COLUMN IF NOT EXISTS favorite BOOLEAN NOT NULL DEFAULT FALSE",
    "ALTER TABLE stories ADD COLUMN IF NOT EXISTS idea_key VARCHAR(64) NOT NULL DEFAULT ''",
    "ALTER TABLE stories ADD COLUMN IF NOT EXISTS metrics JSON",
    "ALTER TABLE stories ADD COLUMN IF NOT EXISTS human_rating JSON",
    "ALTER TABLE scenes ADD COLUMN IF NOT EXISTS status VARCHAR(20) NOT NULL DEFAULT 'ready'",
    "ALTER TABLE scenes ADD COLUMN IF NOT EXISTS error TEXT NOT NULL DEFAULT ''",
    "CREATE INDEX IF NOT EXISTS ix_stories_idea_key ON stories (idea_key)",
]


def init_db() -> None:
    from . import models  # noqa: F401  (register tables)

    Base.metadata.create_all(engine)
    with engine.begin() as conn:
        for stmt in UPGRADES:
            conn.execute(text(stmt))
        # Image jobs don't survive a restart; let the user retry them.
        conn.execute(text(
            "UPDATE scenes SET status='failed', error='Interrupted by a server restart. Use Retry images.' "
            "WHERE status IN ('pending', 'rendering')"
        ))
