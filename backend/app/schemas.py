from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

Strategy = Literal["direct", "interview", "cot", "tot"]


class IdeaInput(BaseModel):
    protagonist: str = Field(min_length=2, max_length=500)
    goal: str = Field(min_length=2, max_length=300)
    genre: str = Field(min_length=2, max_length=120)
    world_rule: str = Field(default="", max_length=300)
    ending_twist: str = Field(default="", max_length=300)


class PlotParameters(BaseModel):
    """Conditioning controls (0-100). These change the PROMPT, not the decoder."""
    tone: int = Field(35, ge=0, le=100)          # 0 = dark, 100 = light
    conflict: int = Field(80, ge=0, le=100)
    romance: int = Field(45, ge=0, le=100)
    action: int = Field(90, ge=0, le=100)
    length: int = Field(60, ge=0, le=100)        # 0 = short, 100 = long


class SamplingParameters(BaseModel):
    """Decoding controls passed straight to the model API."""
    temperature: float = Field(0.9, ge=0.0, le=2.0)
    top_p: float = Field(0.95, ge=0.0, le=1.0)
    top_k: int = Field(40, ge=1, le=100)
    max_output_tokens: int = Field(4096, ge=256, le=8192)
    seed: Optional[int] = None


class GenerateRequest(BaseModel):
    idea: IdeaInput
    plot: PlotParameters = PlotParameters()
    sampling: SamplingParameters = SamplingParameters()
    strategy: Strategy = "direct"


class SceneOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    index: int
    caption: str
    image_prompt: str
    image_url: str
    status: str
    error: str


class RunOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    step: str
    prompt: str
    params: dict
    latency_ms: float


class StoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    title: str
    genre: str
    strategy: str
    provider: str
    model: str
    idea: dict
    plot: dict
    sampling: dict
    output: dict
    artifacts: dict
    idea_key: str
    favorite: bool
    metrics: Optional[dict]
    human_rating: Optional[dict]
    created_at: datetime
    scenes: list[SceneOut]
    runs: list[RunOut]


class StorySummary(BaseModel):
    id: int
    title: str
    genre: str
    logline: str
    strategy: str
    provider: str
    temperature: float
    favorite: bool
    cover_url: str
    scenes_total: int
    scenes_ready: int
    image_status: Literal["ready", "rendering", "failed"]
    created_at: datetime


class HumanRating(BaseModel):
    coherence: int = Field(ge=1, le=5)
    creativity: int = Field(ge=1, le=5)
    adherence: int = Field(ge=1, le=5)
    character_consistency: int = Field(ge=1, le=5)
    notes: str = Field(default="", max_length=1000)


class StoryPatch(BaseModel):
    favorite: Optional[bool] = None
    human_rating: Optional[HumanRating] = None


class UserSettings(BaseModel):
    default_genre: str = "Dark Fantasy"
    default_tone: int = Field(35, ge=0, le=100)
    plot: PlotParameters = PlotParameters()
    strategy: Strategy = "direct"
    sampling: SamplingParameters = SamplingParameters()
