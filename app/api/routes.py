import json

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.repositories.project_repo import ProjectRepository
from app.schemas.brief import ThemeBrief
from app.services.scoring_service import ScoringService
from app.services.generation_service import GenerationService
from app.services.validation_service import ValidationService


router = APIRouter()
repo = ProjectRepository()
scoring = ScoringService()
validator = ValidationService()
generator = GenerationService()


class ScoreRequest(BaseModel):
    answers: dict[str, str]


class GenerationRequest(ThemeBrief):
    name: str = ""
    provider: str = "ark"


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


@router.post("/generation/stream")
async def stream_generation(payload: GenerationRequest) -> StreamingResponse:
    async def event_stream():
        try:
            yield _sse("status", {"message": f"已启动 {payload.provider} 生成链路。"})
            brief = ThemeBrief(**payload.dict(exclude={"name", "provider"}))
            async for item in generator.stream_generate(brief, provider=payload.provider):
                if item["type"] == "reasoning":
                    yield _sse("reasoning", {"delta": item["delta"]})
                elif item["type"] == "output":
                    yield _sse("output", {"delta": item["delta"]})
                elif item["type"] == "completed":
                    config = item["config"]
                    project_name = payload.name.strip() or config.meta.name
                    project_id = repo.create_project(project_name, brief.topic, config.meta.description, config)
                    yield _sse(
                        "project_created",
                        {
                            "project_id": project_id,
                            "editor_url": f"/projects/{project_id}/editor",
                            "preview_url": f"/projects/{project_id}/preview",
                            "provider": item.get("provider", payload.provider),
                        },
                    )
                    yield _sse("done", {"project_id": project_id})
        except Exception as exc:
            yield _sse("error", {"message": str(exc)})
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


def _sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"
