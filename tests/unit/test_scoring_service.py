from pathlib import Path

from app.schemas.test_config import TestConfig
from app.services.scoring_service import ScoringService


def load_config() -> TestConfig:
    return TestConfig.parse_raw(Path("tests/fixtures/sample_config.json").read_text(encoding="utf-8"))


def test_scores_exact_high_template() -> None:
    config = load_config()
    result = ScoringService().score(config, {"q1": "c", "q2": "c", "q3": "c", "q_gate": "a"})

    assert result.result_id == "AAA"
    assert result.similarity == 100
    assert result.user_vector == ["H", "H", "H"]


def test_hidden_rule_overrides_standard_result() -> None:
    config = load_config()
    result = ScoringService().score(config, {"q1": "c", "q2": "c", "q3": "c", "q_gate": "b"})

    assert result.result_id == "HID"
    assert result.triggered_rules == ["HID"]


def test_scores_low_template() -> None:
    config = load_config()
    result = ScoringService().score(config, {"q1": "a", "q2": "a", "q3": "a", "q_gate": "a"})

    assert result.result_id == "BBB"
    assert result.user_vector == ["L", "L", "L"]
