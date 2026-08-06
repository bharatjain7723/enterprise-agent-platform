from openai import AsyncOpenAI

from enterprise_agent_platform.core.settings import get_settings


class LLMClient:
    """Creates configured OpenAI clients."""

    def __init__(self):
        settings = get_settings()

        self.client = AsyncOpenAI(
            api_key=settings.openai_api_key,
        )
