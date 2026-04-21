import json
from pathlib import Path

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import ValidationError

from app.repositories.project_repo import ProjectRepository
from app.schemas.brief import ThemeBrief
from app.schemas.test_config import TestConfig
from app.services.export_service import ExportService
from app.services.generation_service import GenerationService
from app.services.validation_service import ValidationService
from app.web.form_utils import parse_urlencoded_form


router = APIRouter()
templates = Jinja2Templates(directory="app/templates")
repo = ProjectRepository()
generator = GenerationService()
validator = ValidationService()
exporter = ExportService()


@router.get("/", response_class=HTMLResponse)
def index(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        "projects/index.html",
        {"request": request, "projects": repo.list_projects()},
    )


@router.get("/project-docs/mvp")
def mvp_doc() -> FileResponse:
    path = Path("docs/xbti_mvp_requirements_architecture.md")
    if not path.exists():
        raise HTTPException(status_code=404, detail="Document not found")
    return FileResponse(path, media_type="text/markdown; charset=utf-8")


@router.get("/projects/new", response_class=HTMLResponse)
def new_project(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("projects/new.html", {"request": request, "errors": []})


@router.post("/projects")
async def create_project(request: Request):
    form = await parse_urlencoded_form(request)
    errors: list[str] = []
    try:
        brief = ThemeBrief(
            topic=form.get("topic", "").strip(),
            audience=form.get("audience", "").strip() or "泛互联网用户",
            tone=form.get("tone", "").strip() or "抽象、有梗、但最后温柔收住",
            platform=form.get("platform", "").strip() or "社交平台",
            question_count=int(form.get("question_count") or 30),
            dimension_count=int(form.get("dimension_count") or 15),
            result_count=int(form.get("result_count") or 24),
            allow_hidden_results=form.get("allow_hidden_results") == "on",
        )
        config = generator.generate_from_brief(brief)
        name = form.get("name", "").strip() or config.meta.name
        project_id = repo.create_project(name, brief.topic, config.meta.description, config)
        return RedirectResponse(f"/projects/{project_id}/editor", status_code=303)
    except (ValueError, ValidationError) as exc:
        errors.append(str(exc))
    return templates.TemplateResponse("projects/new.html", {"request": request, "errors": errors}, status_code=400)


@router.get("/projects/{project_id}", response_class=HTMLResponse)
def project_detail(project_id: str):
    return RedirectResponse(f"/projects/{project_id}/editor", status_code=303)


@router.get("/projects/{project_id}/editor", response_class=HTMLResponse)
def editor(request: Request, project_id: str) -> HTMLResponse:
    project, config = _load_project_and_config(project_id)
    report = validator.validate_config(config)
    return templates.TemplateResponse(
        "projects/editor.html",
        {
            "request": request,
            "project": project,
            "config": config,
            "config_json": config.json(ensure_ascii=False, indent=2),
            "report": report,
            "errors": [],
            "saved": False,
        },
    )


@router.post("/projects/{project_id}/config", response_class=HTMLResponse)
async def save_config(request: Request, project_id: str) -> HTMLResponse:
    project = repo.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    form = await parse_urlencoded_form(request)
    raw_config = form.get("config_json", "")
    errors: list[str] = []
    saved = False
    try:
        config = TestConfig.parse_raw(raw_config)
        repo.save_config(project_id, config)
        saved = True
    except Exception as exc:
        config = repo.get_current_config(project_id)
        errors.append(str(exc))
    if not config:
        raise HTTPException(status_code=404, detail="Project config not found")
    report = validator.validate_config(config)
    return templates.TemplateResponse(
        "projects/editor.html",
        {
            "request": request,
            "project": project,
            "config": config,
            "config_json": raw_config if errors else config.json(ensure_ascii=False, indent=2),
            "report": report,
            "errors": errors,
            "saved": saved,
        },
        status_code=400 if errors else 200,
    )


@router.get("/projects/{project_id}/preview", response_class=HTMLResponse)
def preview(request: Request, project_id: str) -> HTMLResponse:
    project, config = _load_project_and_config(project_id)
    return templates.TemplateResponse(
        "preview/preview.html",
        {
            "request": request,
            "project": project,
            "config": config,
            "config_json": json.dumps(config.dict(), ensure_ascii=False),
        },
    )


@router.get("/projects/{project_id}/export", response_class=HTMLResponse)
def export_page(request: Request, project_id: str) -> HTMLResponse:
    project, config = _load_project_and_config(project_id)
    report = validator.validate_config(config)
    exports = repo.list_exports(project_id)
    return templates.TemplateResponse(
        "exports/export.html",
        {
            "request": request,
            "project": project,
            "config": config,
            "report": report,
            "exports": exports,
            "errors": [],
        },
    )


@router.post("/projects/{project_id}/export", response_class=HTMLResponse)
async def create_export(request: Request, project_id: str):
    project, config = _load_project_and_config(project_id)
    try:
        export_id = exporter.export_html(project_id, config)
        return RedirectResponse(f"/exports/{export_id}", status_code=303)
    except ValueError as exc:
        report = validator.validate_config(config)
        return templates.TemplateResponse(
            "exports/export.html",
            {
                "request": request,
                "project": project,
                "config": config,
                "report": report,
                "exports": repo.list_exports(project_id),
                "errors": [str(exc)],
            },
            status_code=400,
        )


@router.get("/exports/{export_id}")
def download_export(export_id: str) -> FileResponse:
    export = repo.get_export(export_id)
    if not export:
        raise HTTPException(status_code=404, detail="Export not found")
    return FileResponse(export["file_path"], filename="index.html", media_type="text/html")


def _load_project_and_config(project_id: str) -> tuple[dict, TestConfig]:
    project = repo.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    config = repo.get_current_config(project_id)
    if not config:
        raise HTTPException(status_code=404, detail="Project config not found")
    return project, config
