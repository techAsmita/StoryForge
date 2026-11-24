"""Application settings, loaded from environment variables / backend/.env."""
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=BACKEND_DIR / ".env", env_file_encoding="utf-8", extra="ignore")

    # Database
    database_url: str = "postgresql+psycopg://storyforge:storyforge@localhost:5432/storyforge"

    # LLM: "auto" uses Gemini when GEMINI_API_KEY is set, otherwise the offline mock.
    # Force one with "gemini" or "mock".
    llm_provider: str = "auto"
    gemini_api_key: str = ""
    # Check AI Studio -> Rate limits for the model with the best free daily quota on your key.
    gemini_model: str = "gemini-3.5-flash-lite"

    # Images: "openai" (OpenAI image model, needs OPENAI_API_KEY, paid per image),
    # "pollinations" (free Flux) or "placeholder" (offline cards).
    image_provider: str = "pollinations"
    openai_api_key: str = ""
    openai_image_model: str = "gpt-image-2"
    openai_image_quality: str = "medium"  # low | medium | high (higher costs more per image)
    # Optional free key from enter.pollinations.ai. Without it, anonymous requests are rate limited,
    # so panels are rendered one at a time with IMAGE_MIN_INTERVAL seconds between them.
    pollinations_api_key: str = ""
    image_min_interval: float = 46.0
    image_size: int = 768
    media_dir: Path = BACKEND_DIR / "media"

    cors_origins: str = "http://localhost:5173"

    @property
    def effective_llm(self) -> str:
        if self.llm_provider == "auto":
            return "gemini" if self.gemini_api_key.strip() else "mock"
        return self.llm_provider


@lru_cache
def get_settings() -> Settings:
    return Settings()
