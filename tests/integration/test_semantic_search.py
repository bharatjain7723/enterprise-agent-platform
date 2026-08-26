from datetime import UTC, datetime
from pathlib import Path

import pytest

from enterprise_agent_platform.knowledge.embedding_repository import (
    EmbeddingRepository,
)
from enterprise_agent_platform.knowledge.file_index_store import FileIndexStore
from enterprise_agent_platform.models.embedded_document import (
    EmbeddedDocument,
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
    ) -> None:
        self.embedding = embedding
        self.call_count = 0
        self.last_text: str | None = None

    @property
    def metadata(self) -> EmbeddingMetadata:
        return EmbeddingMetadata(
            provider="fake",
            model="test-model",
            dimensions=3,
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
        raise NotImplementedError


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
    )

    index_store = FileIndexStore(
        tmp_path / "semantic_index.json",
    )

    repository = EmbeddingRepository(
        embedding_service=embedding_service,
        index_store=index_store,
    )

    repository.documents = [
        EmbeddedDocument(
            document=document_a,
            embedding=[1.0, 0.0],
            embedded_at=TEST_TIMESTAMP,
        ),
        EmbeddedDocument(
            document=document_b,
            embedding=[0.0, 1.0],
            embedded_at=TEST_TIMESTAMP,
        ),
        EmbeddedDocument(
            document=document_c,
            embedding=[0.707, 0.707],
            embedded_at=TEST_TIMESTAMP,
        ),
    ]

    documentation_service = DocumentationService(
        searcher=repository,
    )

    results = await documentation_service.search("How does asynchronous Python programming work?")

    assert len(results) == 3

    assert results[0].document.id == "a"
    assert results[1].document.id == "c"
    assert results[2].document.id == "b"
