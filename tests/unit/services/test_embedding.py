from typing import cast

import pytest
from openai import AsyncOpenAI

from enterprise_agent_platform.services.embedding import (
    OpenAIEmbeddingService,
)


class FakeEmbedding:
    def __init__(
        self,
        index: int,
        embedding: list[float],
    ) -> None:
        self.index = index
        self.embedding = embedding


class FakeEmbeddingResponse:
    def __init__(
        self,
        data: list[FakeEmbedding],
    ) -> None:
        self.data = data


class FakeEmbeddingsClient:
    def __init__(self) -> None:
        self.called_with: dict[str, object] = {}

    async def create(
        self,
        *,
        model: str,
        input: str,
    ) -> FakeEmbeddingResponse:
        self.called_with = {
            "model": model,
            "input": input,
        }

        return FakeEmbeddingResponse(
            data=[
                FakeEmbedding(
                    index=1,
                    embedding=[0.4, 0.5, 0.6],
                ),
                FakeEmbedding(
                    index=0,
                    embedding=[0.1, 0.2, 0.3],
                ),
            ]
        )


class FakeOpenAIClient:
    def __init__(self) -> None:
        self.embeddings = FakeEmbeddingsClient()


@pytest.mark.asyncio
async def test_embed_returns_embedding() -> None:
    fake_client = FakeOpenAIClient()

    client = cast(
        AsyncOpenAI,
        fake_client,
    )

    service = OpenAIEmbeddingService(
        client=client,
        model="test-model",
    )

    result = await service.embed("hello")

    assert result == [0.1, 0.2, 0.3]

    assert fake_client.embeddings.called_with == {
        "model": "test-model",
        "input": "hello",
    }


@pytest.mark.asyncio
async def test_embed_many_returns_embeddings() -> None:
    fake_client = FakeOpenAIClient()

    client = cast(
        AsyncOpenAI,
        fake_client,
    )

    service = OpenAIEmbeddingService(
        client=client,
        model="test-model",
    )

    result = await service.embed_many(["hello", "world"])

    assert result == [
        [0.1, 0.2, 0.3],
        [0.4, 0.5, 0.6],
    ]

    assert fake_client.embeddings.called_with == {
        "model": "test-model",
        "input": ["hello", "world"],
    }


@pytest.mark.asyncio
async def test_embedding_service_metadata() -> None:
    fake_client = FakeOpenAIClient()

    client = cast(
        AsyncOpenAI,
        fake_client,
    )

    service = OpenAIEmbeddingService(
        client=client,
        model="test-model",
        dimensions=3200,
    )

    assert service.metadata.provider == "openai"
    assert service.metadata.model == "test-model"
    assert service.metadata.dimensions == 3200
    assert service.metadata.index_version == 1
