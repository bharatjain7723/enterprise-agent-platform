from datetime import UTC, datetime
from pathlib import Path

import pytest
from qdrant_client import AsyncQdrantClient

from enterprise_agent_platform.knowledge.embedding_repository import (
    EmbeddingRepository,
)
from enterprise_agent_platform.knowledge.file_index_store import FileIndexStore
from enterprise_agent_platform.knowledge.qdrant_vector_store import (
    QdrantVectorStore,
)
from enterprise_agent_platform.models.embedding_metadata import EmbeddingMetadata
from enterprise_agent_platform.models.knowledge_document import (
    KnowledgeDocument,
)
from enterprise_agent_platform.services.documentation import (
    DocumentationService,
)

TEST_TIMESTAMP = datetime(
    2026,
    8,
    22,
    10,
    0,
    tzinfo=UTC,
)


class FakeEmbeddingService:
    def __init__(
        self,
        embedding: list[float],
        embeddings: list[list[float]],
    ) -> None:
        self.embedding = embedding
        self.embeddings = embeddings
        self.call_count = 0
        self.embed_many_call_count = 0
        self.last_text: str | None = None
        self.last_texts: list[str] | None = None

    @property
    def metadata(self) -> EmbeddingMetadata:
        return EmbeddingMetadata(
            provider="fake",
            model="test-model",
            dimensions=2,
            index_version=1,
        )

    async def embed(
        self,
        text: str,
    ) -> list[float]:
        self.call_count += 1
        self.last_text = text
        return self.embedding

    async def embed_many(
        self,
        texts: list[str],
    ) -> list[list[float]]:
        self.embed_many_call_count += 1
        self.last_texts = texts
        return self.embeddings


@pytest.mark.asyncio
async def test_documentation_service_performs_semantic_search(
    tmp_path: Path,
) -> None:
    document_a = KnowledgeDocument(
        id="a",
        title="AsyncIO",
        content="Asynchronous programming in Python.",
        source="",
        updated_at=TEST_TIMESTAMP,
    )

    document_b = KnowledgeDocument(
        id="b",
        title="Databases",
        content="Database indexing and queries.",
        source="",
        updated_at=TEST_TIMESTAMP,
    )

    document_c = KnowledgeDocument(
        id="c",
        title="Concurrency",
        content="Concurrent programming concepts.",
        source="",
        updated_at=TEST_TIMESTAMP,
    )

    embedding_service = FakeEmbeddingService(
        embedding=[1.0, 0.0],
        embeddings=[
            [1.0, 0.0],
            [0.0, 1.0],
            [0.707, 0.707],
        ],
    )

    index_store = FileIndexStore(
        tmp_path / "semantic_index.json",
    )

    client = AsyncQdrantClient(
        location=":memory:",
    )

    vector_store = QdrantVectorStore(
        client=client,
        collection_name="test_documents",
        dimensions=2,
    )

    await vector_store.initialize()

    repository = EmbeddingRepository(
        embedding_service=embedding_service,
        index_store=index_store,
        vector_store=vector_store,
    )

    await repository.index_documents(
        [
            document_a,
            document_b,
            document_c,
        ]
    )

    documentation_service = DocumentationService(
        searcher=repository,
    )

    results = await documentation_service.search("How does asynchronous Python programming work?")

    assert len(results) == 3
    assert results[0].document.id == "a"
    assert results[1].document.id == "c"
    assert results[2].document.id == "b"

    await client.close()
