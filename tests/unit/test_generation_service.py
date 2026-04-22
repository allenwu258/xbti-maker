from app.schemas.brief import ThemeBrief
from app.services.ark_generation import ArkGenerationProvider
from app.services.local_generation import LocalGenerationProvider


def test_local_generation_stream_completes() -> None:
    provider = LocalGenerationProvider()
    brief = ThemeBrief(topic="打工人精神状态", question_count=6, dimension_count=3, result_count=3)

    async def collect():
        items = []
        async for item in provider.stream_generate(brief):
            items.append(item)
        return items

    import asyncio

    events = asyncio.run(collect())
    assert any(item["type"] == "reasoning" for item in events)
    assert any(item["type"] == "output" for item in events)
    completed = next(item for item in events if item["type"] == "completed")
    assert completed["config"].meta.name.endswith("XBTI")


def test_ark_payload_uses_json_schema_and_stream() -> None:
    provider = ArkGenerationProvider()
    brief = ThemeBrief(topic="奶茶人格", question_count=6, dimension_count=3, result_count=3)

    payload = provider.build_request_payload(brief)

    assert payload["model"]
    assert payload["stream"] is True
    assert payload["thinking"]["type"] == "enabled"
    assert payload["text"]["format"]["type"] == "json_schema"
    assert payload["text"]["format"]["name"] == "xbti_test_config"


def test_ark_provider_extracts_json_from_fenced_block() -> None:
    provider = ArkGenerationProvider()
    raw = """```json
{"meta":{"schema_version":"1.0","test_id":"x","name":"n","subtitle":"","description":"","disclaimer":"d"},"dimension_groups":[],"dimensions":[],"questions":[],"results":[],"rules":[],"scoring":{"algorithm":"level_distance","level_mode":"normalized","low_max":0.4,"mid_max":0.65,"fallback_result_id":"MIXED","min_similarity":60,"shuffle_questions":true},"page":{"theme":"clean_fun","primary_color":"#111111","accent_color":"#2f9e44","start_button_text":"开始测试","result_button_text":"再测一次"}}
```"""

    extracted = provider._extract_json(raw)

    assert extracted.startswith("{")
    assert extracted.endswith("}")
