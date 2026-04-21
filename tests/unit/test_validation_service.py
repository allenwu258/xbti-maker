from pathlib import Path

from app.schemas.test_config import TestConfig
from app.services.validation_service import ValidationService


def load_config() -> TestConfig:
    return TestConfig.parse_raw(Path("tests/fixtures/sample_config.json").read_text(encoding="utf-8"))


def test_valid_sample_has_no_errors() -> None:
    report = ValidationService().validate_config(load_config())

    assert report.can_export
    assert report.errors == []


def test_template_length_mismatch_is_error() -> None:
    config = load_config()
    config.results[0].template = ["H"]

    report = ValidationService().validate_config(config)

    assert not report.can_export
    assert any(issue.code == "template_length_mismatch" for issue in report.errors)
