from pydantic import BaseModel, Field


class ThemeBrief(BaseModel):
    topic: str = Field(..., min_length=1)
    audience: str = "泛互联网用户"
    tone: str = "抽象、有梗、但最后温柔收住"
    platform: str = "社交平台"
    question_count: int = Field(30, ge=6, le=80)
    dimension_count: int = Field(15, ge=3, le=24)
    result_count: int = Field(24, ge=3, le=60)
    allow_hidden_results: bool = True
    safety_level: str = "normal"
