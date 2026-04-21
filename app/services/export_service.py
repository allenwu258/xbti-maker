import json
from datetime import datetime
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from app.core.config import APP_DIR, EXPORTS_DIR
from app.repositories.project_repo import ProjectRepository
from app.schemas.test_config import TestConfig
from app.services.validation_service import ValidationService


class ExportService:
    def __init__(self) -> None:
        self.repo = ProjectRepository()
        self.validator = ValidationService()
        self.templates = Environment(
            loader=FileSystemLoader(str(APP_DIR / "templates")),
            autoescape=select_autoescape(["html"]),
        )

    def export_html(self, project_id: str, config: TestConfig) -> str:
        report = self.validator.validate_config(config)
        if not report.can_export:
            messages = "; ".join(issue.message for issue in report.errors)
            raise ValueError(f"导出前检查未通过: {messages}")

        version = self.repo.get_current_version(project_id)
        if not version:
            raise ValueError("项目没有当前版本。")

        runtime = (APP_DIR / "static" / "js" / "exported_runtime.js").read_text(encoding="utf-8")
        css = (APP_DIR / "static" / "css" / "exported.css").read_text(encoding="utf-8")
        template = self.templates.get_template("exported/standalone.html")
        config_json = json.dumps(config.dict(), ensure_ascii=False)
        html = template.render(config=config, config_json=config_json, runtime_js=runtime, exported_css=css)

        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        export_dir = EXPORTS_DIR / project_id / stamp
        export_dir.mkdir(parents=True, exist_ok=True)
        file_path = export_dir / "index.html"
        file_path.write_text(html, encoding="utf-8")

        return self.repo.create_export(project_id, version["id"], str(file_path))
