from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.repositories.project_repo import ProjectRepository
from app.services.scoring_service import ScoringService
from app.services.validation_service import ValidationService


router = APIRouter()
repo = ProjectRepository()
scoring = ScoringService()
validator = ValidationService()


class ScoreRequest(BaseModel):
    answers: dict[str, str]


@router.get("/projects/{project_id}/config")
def get_config(project_id: str) -> dict:
    config = repo.get_current_config(project_id)
    if not config:
        raise HTTPException(status_code=404, detail="Project config not found")
    return config.dict()


@router.post("/projects/{project_id}/validate")
def validate_config(project_id: str) -> dict:
    config = repo.get_current_config(project_id)
    if not config:
        raise HTTPException(status_code=404, detail="Project config not found")
    return validator.validate_config(config).dict()


@router.post("/projects/{project_id}/score")
def score(project_id: str, payload: ScoreRequest) -> dict:
    config = repo.get_current_config(project_id)
    if not config:
        raise HTTPException(status_code=404, detail="Project config not found")
    return scoring.score(config, payload.answers).dict()
