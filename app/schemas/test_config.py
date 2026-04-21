from typing import Literal, Optional

from pydantic import BaseModel, Field, validator


Level = Literal["L", "M", "H"]
QuestionType = Literal["single_choice"]
ResultKind = Literal["standard", "hidden", "fallback"]
RuleType = Literal["answer_equals"]


class TestMeta(BaseModel):
    schema_version: str = "1.0"
    test_id: str
    name: str
    subtitle: str = ""
    description: str = ""
    disclaimer: str = "本测试仅供娱乐，不构成心理诊断或专业建议。"


class DimensionGroup(BaseModel):
    id: str
    name: str
    description: str = ""


class Dimension(BaseModel):
    id: str
    group_id: str
    name: str
    description: str = ""
    low_label: str
    mid_label: str
    high_label: str
    weight: float = Field(1.0, gt=0)


class OptionConfig(BaseModel):
    id: str
    text: str
    score: Optional[float] = None


class DisplayCondition(BaseModel):
    question_id: str
    option_id: str


class Question(BaseModel):
    id: str
    text: str
    type: QuestionType = "single_choice"
    dimension_id: Optional[str] = None
    is_scored: bool = True
    is_gate: bool = False
    display_condition: Optional[DisplayCondition] = None
    options: list[OptionConfig]

    @validator("options")
    def require_options(cls, value: list[OptionConfig]) -> list[OptionConfig]:
        if len(value) < 2:
            raise ValueError("question must have at least two options")
        return value


class ResultConfig(BaseModel):
    id: str
    code: str
    name: str
    kind: ResultKind = "standard"
    template: list[Level] = Field(default_factory=list)
    priority: int = 0
    headline: str
    description: str
    share_text: str = ""


class RuleConfig(BaseModel):
    id: str
    type: RuleType = "answer_equals"
    question_id: str
    option_id: str
    result_id: str
    priority: int = 0


class ScoringConfig(BaseModel):
    algorithm: Literal["level_distance"] = "level_distance"
    level_mode: Literal["normalized"] = "normalized"
    low_max: float = Field(0.4, ge=0, le=1)
    mid_max: float = Field(0.65, ge=0, le=1)
    fallback_result_id: str = "MIXED"
    min_similarity: int = Field(60, ge=0, le=100)
    shuffle_questions: bool = True


class PageConfig(BaseModel):
    theme: str = "clean_fun"
    primary_color: str = "#111111"
    accent_color: str = "#2f9e44"
    start_button_text: str = "开始测试"
    result_button_text: str = "再测一次"


class TestConfig(BaseModel):
    meta: TestMeta
    dimension_groups: list[DimensionGroup]
    dimensions: list[Dimension]
    questions: list[Question]
    results: list[ResultConfig]
    rules: list[RuleConfig] = Field(default_factory=list)
    scoring: ScoringConfig = Field(default_factory=ScoringConfig)
    page: PageConfig = Field(default_factory=PageConfig)
