import json
from collections.abc import AsyncIterator, Iterable
from typing import Optional

import httpx

from app.core.config import (
    get_ark_api_key,
    get_ark_model_id,
    get_ark_reasoning_effort,
    get_ark_responses_url,
)
from app.schemas.brief import ThemeBrief
from app.schemas.test_config import TestConfig


class ArkConfigurationError(RuntimeError):
    pass


class ArkGenerationError(RuntimeError):
    pass


class ArkGenerationProvider:
    def __init__(self) -> None:
        self.endpoint = get_ark_responses_url()
        self.model_id = get_ark_model_id()
        self.reasoning_effort = get_ark_reasoning_effort()

    def build_request_payload(self, brief: ThemeBrief) -> dict:
        schema = TestConfig.schema()
        schema.pop("title", None)
        schema.setdefault("additionalProperties", False)
        return {
            "model": self.model_id,
            "input": [
                {
                    "type": "message",
                    "role": "developer",
                    "content": [
                        {
                            "type": "input_text",
                            "text": self._developer_prompt(),
                        }
                    ],
                },
                {
                    "type": "message",
                    "role": "user",
                    "content": [
                        {
                            "type": "input_text",
                            "text": self._user_prompt(brief),
                        }
                    ],
                },
            ],
            "stream": True,
            "store": False,
            "thinking": {"type": "enabled"},
            "reasoning": {"effort": self.reasoning_effort},
            "max_output_tokens": 12000,
            "temperature": 0.7,
            "text": {
                "format": {
                    "type": "json_schema",
                    "name": "xbti_test_config",
                    "description": "生成一个可直接被 XBTI Maker 使用的完整测试配置。",
                    "schema": schema,
                    "strict": True,
                }
            },
        }

    async def stream_generate(self, brief: ThemeBrief) -> AsyncIterator[dict]:
        api_key = get_ark_api_key()
        if not api_key:
            raise ArkConfigurationError("ARK_API_KEY 未配置，暂时无法调用方舟模型。")

        payload = self.build_request_payload(brief)
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Accept": "text/event-stream",
        }

        output_fragments: list[str] = []
        reasoning_fragments: list[str] = []

        timeout = httpx.Timeout(connect=20.0, read=None, write=60.0, pool=60.0)
        async with httpx.AsyncClient(timeout=timeout) as client:
            async with client.stream("POST", self.endpoint, headers=headers, json=payload) as response:
                if response.status_code >= 400:
                    detail = await response.aread()
                    raise ArkGenerationError(
                        f"Ark Responses API 调用失败: HTTP {response.status_code} {detail.decode('utf-8', errors='ignore')}"
                    )

                async for event in self._iter_sse_events(response):
                    event_type = event.get("type") or "message"
                    if event_type == "response.reasoning_summary_text.delta":
                        delta = self._extract_text_fragment(event, "delta")
                        if delta:
                            reasoning_fragments.append(delta)
                            yield {"type": "reasoning", "delta": delta}
                    elif event_type == "response.output_text.delta":
                        delta = self._extract_text_fragment(event, "delta")
                        if delta:
                            output_fragments.append(delta)
                            yield {"type": "output", "delta": delta}
                    elif event_type in {"response.failed", "error"}:
                        raise ArkGenerationError(self._extract_error_message(event))
                    elif event_type == "response.completed":
                        continue

        raw_output = "".join(output_fragments).strip()
        config = self.parse_generated_config(raw_output)
        yield {
            "type": "completed",
            "config": config,
            "raw_output": raw_output,
            "reasoning_text": "".join(reasoning_fragments),
            "provider": "ark",
        }

    async def _iter_sse_events(self, response: httpx.Response) -> AsyncIterator[dict]:
        event_name: Optional[str] = None
        data_lines: list[str] = []

        async for line in response.aiter_lines():
            if line.startswith("event:"):
                event_name = line.split(":", 1)[1].strip()
                continue
            if line.startswith("data:"):
                data_lines.append(line.split(":", 1)[1].strip())
                continue
            if line.strip():
                continue
            if not data_lines:
                event_name = None
                continue
            payload = self._decode_sse_payload(data_lines, event_name)
            if payload is not None:
                yield payload
            event_name = None
            data_lines = []

        if data_lines:
            payload = self._decode_sse_payload(data_lines, event_name)
            if payload is not None:
                yield payload

    def _decode_sse_payload(self, data_lines: Iterable[str], event_name: Optional[str]) -> Optional[dict]:
        raw = "\n".join(data_lines).strip()
        if not raw or raw == "[DONE]":
            return None
        payload = json.loads(raw)
        if event_name and "type" not in payload:
            payload["type"] = event_name
        return payload

    def parse_generated_config(self, raw_output: str) -> TestConfig:
        cleaned = self._extract_json(raw_output)
        return TestConfig.parse_raw(cleaned)

    def _extract_json(self, raw_output: str) -> str:
        text = raw_output.strip()
        if text.startswith("```"):
            lines = text.splitlines()
            if lines and lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].startswith("```"):
                lines = lines[:-1]
            text = "\n".join(lines).strip()

        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise ArkGenerationError("模型没有返回可解析的 JSON 配置。")
        return text[start : end + 1]

    def _extract_text_fragment(self, payload: dict, key: str) -> str:
        if isinstance(payload.get(key), str):
            return payload[key]
        if isinstance(payload.get("text"), str):
            return payload["text"]
        part = payload.get("part")
        if isinstance(part, dict):
            if isinstance(part.get(key), str):
                return part[key]
            if isinstance(part.get("text"), str):
                return part["text"]
        summary = payload.get("summary")
        if isinstance(summary, list):
            fragments = [item.get("text", "") for item in summary if isinstance(item, dict)]
            return "".join(fragment for fragment in fragments if fragment)
        return ""

    def _extract_error_message(self, payload: dict) -> str:
        if isinstance(payload.get("error"), dict):
            error = payload["error"]
            message = error.get("message") or error.get("type") or str(error)
            return f"Ark 流式响应失败: {message}"
        return f"Ark 流式响应失败: {json.dumps(payload, ensure_ascii=False)}"

    def _developer_prompt(self) -> str:
        return (
            "你是 XBTI Maker 的资深测试策划与结构化配置生成器。"
            "你的任务是根据用户给出的主题 brief，输出一份完整、可执行、可导出的趣味人格测试配置。"
            "配置必须适合年轻互联网用户传播，但不得直接复制 MBTI 或 SBTI 的现有题目、人格名与文案。"
            "务必满足以下要求："
            "1. 输出必须是合法 JSON，且严格符合给定 schema；"
            "2. 保持娱乐化，但不得做医疗、心理诊断、歧视、羞辱、暴力、自残鼓励；"
            "3. 题目、维度、结果之间要有可解释关系；"
            "4. 每个标准人格 template 长度必须等于维度数；"
            "5. fallback 结果必须存在且 id 为 MIXED；"
            "6. 结果文案要有传播感，但最后要有理解和回收，不要只是一味攻击用户；"
            "7. 整体风格要符合用户给出的 tone 与 platform。"
        )

    def _user_prompt(self, brief: ThemeBrief) -> str:
        hidden_hint = "需要至少 1 个隐藏人格和对应规则。" if brief.allow_hidden_results else "不要生成隐藏人格。"
        return (
            f"请基于以下 brief 生成一份完整 XBTI 测试配置：\n"
            f"- 主题: {brief.topic}\n"
            f"- 目标人群: {brief.audience}\n"
            f"- 语气风格: {brief.tone}\n"
            f"- 传播平台: {brief.platform}\n"
            f"- 正式题数量: {brief.question_count}\n"
            f"- 维度数量: {brief.dimension_count}\n"
            f"- 结果人格数量: {brief.result_count}\n"
            f"- 内容安全级别: {brief.safety_level}\n"
            f"- 隐藏人格要求: {hidden_hint}\n\n"
            "请让结构体现以下设计原则：\n"
            "1. 维度尽量分布在自我、关系、世界、行动、表达等模型组；\n"
            "2. 每个维度都要有 low/mid/high 三档可解释描述；\n"
            "3. 正式题以 3 选项单选题为主，选项 score 使用 1/2/3；\n"
            "4. 结果人格要短、好记、适合截图传播；\n"
            "5. 页面文案要让用户可以直接在 H5 中使用。\n"
        )
