from openai import AsyncOpenAI

from enterprise_agent_platform.models.embedding_metadata import (
    EmbeddingMetadata,
)


class OpenAIEmbeddingService:
    """Generates embeddings using OpenAI."""

    def __init__(
        self,
        client: AsyncOpenAI,
        model: str = "text-embedding-3-small",
        dimensions: int = 1536,
    ) -> None:
        self.client = client
        self.model = model
        self.dimensions = dimensions

    @property
    def metadata(self) -> EmbeddingMetadata:
        return EmbeddingMetadata(
            provider="openai",
            model=self.model,
            dimensions=self.dimensions,
            index_version=1,
        )

    async def embed(
        self,
        text: str,
    ) -> list[float]:
        if not text.strip():
            raise ValueError("Text cannot be empty.")

        response = await self.client.embeddings.create(
            model=self.model,
            input=text,
        )

        for item in response.data:
            if item.index == 0:
                return item.embedding

        raise ValueError("Embedding response did not contain an embedding for index 0.")

    async def embed_many(
        self,
        texts: list[str],
    ) -> list[list[float]]:
        if not texts:
            return []

        response = await self.client.embeddings.create(
            model=self.model,
            input=texts,
        )

        embeddings: list[list[float] | None] = [None] * len(texts)

        for item in response.data:
            embeddings[item.index] = item.embedding

        if any(embedding is None for embedding in embeddings):
            raise RuntimeError("Embedding response did not contain all requested embeddings.")

        return [embedding for embedding in embeddings if embedding is not None]
