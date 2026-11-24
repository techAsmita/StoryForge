"""PostgreSQL tables.

stories          one generated story (inputs, final structured output, metrics, human rating)
generation_runs  every LLM call made for a story: step, prompt, parameters, raw output, latency
scenes           storyboard panels: caption, full image prompt, image file, render status
app_settings     single row of user defaults (generation parameters etc.)
"""
from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base


class Story(Base):
    __tablename__ = "stories"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(300))
    genre: Mapped[str] = mapped_column(String(120), default="")
    strategy: Mapped[str] = mapped_column(String(40))
    provider: Mapped[str] = mapped_column(String(40))
    model: Mapped[str] = mapped_column(String(120))
    idea: Mapped[dict] = mapped_column(JSON)
    plot: Mapped[dict] = mapped_column(JSON)
    sampling: Mapped[dict] = mapped_column(JSON)
    output: Mapped[dict] = mapped_column(JSON)
    artifacts: Mapped[dict] = mapped_column(JSON, default=dict)
    # Same idea + plot settings -> same key, so runs with different strategies/sampling can be compared.
    idea_key: Mapped[str] = mapped_column(String(64), default="", index=True)
    favorite: Mapped[bool] = mapped_column(Boolean, default=False)
    metrics: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    human_rating: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    runs: Mapped[list["GenerationRun"]] = relationship(back_populates="story", cascade="all, delete-orphan")
    scenes: Mapped[list["Scene"]] = relationship(
        back_populates="story", cascade="all, delete-orphan", order_by="Scene.index"
    )


class GenerationRun(Base):
    __tablename__ = "generation_runs"

    id: Mapped[int] = mapped_column(primary_key=True)
    story_id: Mapped[int] = mapped_column(ForeignKey("stories.id", ondelete="CASCADE"), index=True)
    step: Mapped[str] = mapped_column(String(60))
    prompt: Mapped[str] = mapped_column(Text)
    params: Mapped[dict] = mapped_column(JSON)
    raw_output: Mapped[str] = mapped_column(Text)
    latency_ms: Mapped[float] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    story: Mapped[Story] = relationship(back_populates="runs")


class Scene(Base):
    __tablename__ = "scenes"

    id: Mapped[int] = mapped_column(primary_key=True)
    story_id: Mapped[int] = mapped_column(ForeignKey("stories.id", ondelete="CASCADE"), index=True)
    index: Mapped[int] = mapped_column(Integer)
    caption: Mapped[str] = mapped_column(Text)
    image_prompt: Mapped[str] = mapped_column(Text)
    image_url: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(20), default="pending")  # pending | rendering | ready | failed
    error: Mapped[str] = mapped_column(Text, default="")

    story: Mapped[Story] = relationship(back_populates="scenes")


class AppSetting(Base):
    __tablename__ = "app_settings"

    id: Mapped[int] = mapped_column(primary_key=True)
    data: Mapped[dict] = mapped_column(JSON, default=dict)
