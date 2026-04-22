from collections.abc import AsyncIterator

from app.core.config import ark_enabled
from app.schemas.brief import ThemeBrief
from app.schemas.test_config import TestConfig
from app.services.ark_generation import ArkConfigurationError, ArkGenerationProvider
from app.services.local_generation import LocalGenerationProvider


class GenerationService:
    def __init__(self) -> None:
        self.local_provider = LocalGenerationProvider()
        self.ark_provider = ArkGenerationProvider()

    def generate_from_brief(self, brief: ThemeBrief) -> TestConfig:
        return self.local_provider.generate_from_brief(brief)

    def supports_ark(self) -> bool:
        return ark_enabled()

    async def stream_generate(self, brief: ThemeBrief, provider: str = "ark") -> AsyncIterator[dict]:
        provider = (provider or "ark").strip().lower()
        if provider == "ark":
            if not self.supports_ark():
                raise ArkConfigurationError("ARK_API_KEY 未配置。请先配置 key，或先切到本地模拟模式。")
            async for item in self.ark_provider.stream_generate(brief):
                yield item
            return

        async for item in self.local_provider.stream_generate(brief):
            yield item
