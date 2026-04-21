from pathlib import Path

from app.schemas.test_config import TestConfig
from app.services.export_service import ExportService


def test_standalone_template_contains_runtime_and_config() -> None:
    config = TestConfig.parse_raw(Path("tests/fixtures/sample_config.json").read_text(encoding="utf-8"))
    css = Path("app/static/css/exported.css").read_text(encoding="utf-8")
    runtime = Path("app/static/js/exported_runtime.js").read_text(encoding="utf-8")
    template = ExportService().templates.get_template("exported/standalone.html")
    html = template.render(config=config, config_json=config.json(ensure_ascii=False), runtime_js=runtime, exported_css=css)

    assert "xbti-config" in html
    assert "calculateScore" in html
    assert "样例 XBTI" in html
    assert '"schema_version"' in html
    assert "{&#34;" not in html
    assert "JSON.parse(configEl.textContent)" in html
