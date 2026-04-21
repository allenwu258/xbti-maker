from pydantic import BaseModel


class CandidateScore(BaseModel):
    result_id: str
    code: str
    name: str
    distance: float
    exact_matches: int
    similarity: int
    priority: int


class ScoreResult(BaseModel):
    result_id: str
    similarity: int
    dimension_scores: dict[str, float]
    dimension_levels: dict[str, str]
    user_vector: list[str]
    candidates: list[CandidateScore]
    triggered_rules: list[str]
