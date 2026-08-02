from core.settings import get_settings
from openai import AsyncOpenAI


class LLMClient:
    """Creates configured OpenAI clients."""

    def __init__(self):
        settings = get_settings()

        self.client = AsyncOpenAI(
            api_key=settings.openai_api_key,
        )
