from datetime import UTC, datetime

import pytest

from enterprise_agent_platform.knowledge.embedding_repository import (
    EmbeddingRepository,
)
from enterprise_agent_platform.models.embedded_document import (
    EmbeddedDocument,
)
from enterprise_agent_platform.models.embedding_metadata import (
    EmbeddingMetadata,
)
from enterprise_agent_platform.models.knowledge_document import (
    KnowledgeDocument,
)
from enterprise_agent_platform.models.knowledge_search_result import KnowledgeSearchResult
from enterprise_agent_platform.models.semantic_index import SemanticIndex
from enterprise_agent_platform.services.documentation import DocumentationService

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
        embedding: list[float] | None = None,
        embeddings: list[list[float]] | None = None,
        error: Exception | None = None,
    ) -> None:
        self.embedding = embedding if embedding is not None else [1.0, 0.0]

        self.embeddings = embeddings if embeddings is not None else []
        self.error = error

        self.embed_call_count = 0
        self.embed_many_call_count = 0

        self.last_text: str | None = None
        self.last_texts: list[str] | None = None

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
        self.embed_call_count += 1
        self.last_text = text

        if self.error is not None:
            raise self.error

        return self.embedding

    async def embed_many(
        self,
        texts: list[str],
    ) -> list[list[float]]:
        self.embed_many_call_count += 1
        self.last_texts = texts

        if self.error is not None:
            raise self.error

        return self.embeddings


class FailingEmbeddingService:
    @property
    def metadata(self) -> EmbeddingMetadata: ...

    async def embed(
        self,
        text: str,
    ) -> list[float]:
        raise RuntimeError("Embedding service failed")

    async def embed_many(
        self,
        texts: list[str],
    ) -> list[list[float]]:
        raise NotImplementedError


class FakeDocumentationSearcher:
    def __init__(
        self,
        results: list[KnowledgeSearchResult],
    ) -> None:
        self.results = results
        self.last_query: str | None = None

    async def search(
        self,
        query: str,
    ) -> list[KnowledgeSearchResult]:
        self.last_query = query
        return self.results


class FakeIndexStore:
    def __init__(self) -> None:
        self.index = None
        self.save_calls = 0

    async def save(
        self,
        index: SemanticIndex,
    ) -> None:
        self.index = index
        self.save_calls += 1

    async def load(self) -> SemanticIndex | None:
        return self.index


class FailingIndexStore:
    async def save(
        self,
        index: SemanticIndex,
    ) -> None:
        raise RuntimeError("Storage failed")

    async def load(self) -> SemanticIndex | None:
        return None


@pytest.mark.asyncio
async def test_search_returns_results_sorted_by_similarity() -> None:
    document_a = KnowledgeDocument(
        id="asyncio",
        title="AsyncIO",
        content="Asynchronous programming in Python.",
        source="",
        updated_at=TEST_TIMESTAMP,
    )

    document_b = KnowledgeDocument(
        id="python",
        title="Python",
        content="Python programming language.",
        source="",
        updated_at=TEST_TIMESTAMP,
    )

    embedding_service = FakeEmbeddingService(
        embedding=[1.0, 0.0],
    )

    index_store = FakeIndexStore()

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
    ]

    results = await repository.search("How does asyncio work?")

    assert len(results) == 2

    assert results[0].document.id == "asyncio"
    assert results[0].score == pytest.approx(1.0)

    assert results[1].document.id == "python"
    assert results[1].score == pytest.approx(0.0)


@pytest.mark.asyncio
async def test_search_embeds_query_once() -> None:
    embedding_service = FakeEmbeddingService(
        embedding=[1.0, 0.0],
    )

    index_store = FakeIndexStore()

    repository = EmbeddingRepository(
        embedding_service=embedding_service,
        index_store=index_store,
    )

    repository.documents = [
        EmbeddedDocument(
            document=KnowledgeDocument(
                id="doc-1",
                title="Document 1",
                content="Content 1",
                source="",
                updated_at=TEST_TIMESTAMP,
            ),
            embedding=[1.0, 0.0],
            embedded_at=TEST_TIMESTAMP,
        ),
        EmbeddedDocument(
            document=KnowledgeDocument(
                id="doc-2",
                title="Document 2",
                content="Content 2",
                source="",
                updated_at=TEST_TIMESTAMP,
            ),
            embedding=[0.0, 1.0],
            embedded_at=TEST_TIMESTAMP,
        ),
    ]

    await repository.search("asyncio")

    assert embedding_service.embed_call_count == 1
    assert embedding_service.last_text == "asyncio"


@pytest.mark.asyncio
async def test_search_rejects_empty_query() -> None:
    embedding_service = FakeEmbeddingService(
        embedding=[1.0, 0.0],
    )

    index_store = FakeIndexStore()

    repository = EmbeddingRepository(
        embedding_service=embedding_service,
        index_store=index_store,
    )

    with pytest.raises(
        ValueError,
        match="Query cannot be empty",
    ):
        await repository.search("")


@pytest.mark.asyncio
async def test_search_rejects_whitespace_query() -> None:
    embedding_service = FakeEmbeddingService(
        embedding=[1.0, 0.0],
    )

    index_store = FakeIndexStore()

    repository = EmbeddingRepository(
        embedding_service=embedding_service,
        index_store=index_store,
    )

    with pytest.raises(
        ValueError,
        match="Query cannot be empty",
    ):
        await repository.search("   ")


@pytest.mark.asyncio
async def test_search_returns_empty_list_when_repository_is_empty() -> None:
    embedding_service = FakeEmbeddingService(
        embedding=[1.0, 0.0],
    )

    index_store = FakeIndexStore()

    repository = EmbeddingRepository(
        embedding_service=embedding_service,
        index_store=index_store,
    )

    results = await repository.search("asyncio")

    assert results == []
    assert embedding_service.embed_many_call_count == 0


@pytest.mark.asyncio
async def test_search_propagates_embedding_error() -> None:
    index_store = FakeIndexStore()

    repository = EmbeddingRepository(
        embedding_service=FailingEmbeddingService(), index_store=index_store
    )

    repository.documents = [
        EmbeddedDocument(
            document=KnowledgeDocument(
                id="doc-1",
                title="Document 1",
                content="Content 1",
                source="",
                updated_at=TEST_TIMESTAMP,
            ),
            embedding=[1.0, 0.0],
            embedded_at=TEST_TIMESTAMP,
        ),
    ]

    with pytest.raises(
        RuntimeError,
        match="Embedding service failed",
    ):
        await repository.search("asyncio")


@pytest.mark.asyncio
async def test_search_preserves_document_embedding_relationship() -> None:
    document_a = KnowledgeDocument(
        id="a",
        title="Document A",
        content="A",
        source="",
        updated_at=TEST_TIMESTAMP,
    )

    document_b = KnowledgeDocument(
        id="b",
        title="Document B",
        content="B",
        source="",
        updated_at=TEST_TIMESTAMP,
    )

    embedding_service = FakeEmbeddingService(
        embedding=[0.0, 1.0],
    )

    index_store = FakeIndexStore()

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
    ]

    results = await repository.search("query")

    assert results[0].document.id == "b"
    assert results[0].score == pytest.approx(1.0)


@pytest.mark.asyncio
async def test_documentation_service_searches_documentation() -> None:
    searcher = FakeDocumentationSearcher(
        results=[],
    )

    service = DocumentationService(
        searcher=searcher,
    )

    await service.search("asyncio")

    assert searcher.last_query == "asyncio"


@pytest.mark.asyncio
async def test_documentation_service_returns_search_results() -> None:
    document_a = KnowledgeDocument(
        id="asyncio",
        title="AsyncIO",
        content="Asynchronous programming in Python.",
        source="",
        updated_at=TEST_TIMESTAMP,
    )

    expected_results = [
        KnowledgeSearchResult(
            document=document_a,
            score=1.0,
            snippet="",
        )
    ]

    searcher = FakeDocumentationSearcher(
        results=expected_results,
    )

    service = DocumentationService(
        searcher=searcher,
    )

    results = await service.search("asyncio")

    assert results == expected_results


@pytest.mark.asyncio
async def test_index_documents_creates_embedded_documents() -> None:
    document_a = KnowledgeDocument(
        id="asyncio",
        title="AsyncIO",
        content="Asynchronous programming in Python.",
        source="",
        updated_at=TEST_TIMESTAMP,
    )

    document_b = KnowledgeDocument(
        id="pydantic",
        title="Pydantic",
        content="Data validation using Python.",
        source="",
        updated_at=TEST_TIMESTAMP,
    )

    embeddings = [
        [1.0, 0.0],
        [0.0, 1.0],
    ]

    embedding_service = FakeEmbeddingService(
        embeddings=embeddings,
    )

    index_store = FakeIndexStore()

    repository = EmbeddingRepository(
        embedding_service=embedding_service,
        index_store=index_store,
    )

    await repository.index_documents([document_a, document_b])

    assert len(repository.documents) == 2

    assert repository.documents[0].document == document_a
    assert repository.documents[0].embedding == [1.0, 0.0]

    assert repository.documents[1].document == document_b
    assert repository.documents[1].embedding == [0.0, 1.0]

    assert embedding_service.embed_many_call_count == 1


@pytest.mark.asyncio
async def test_index_documents_with_empty_list() -> None:
    embedding_service = FakeEmbeddingService()

    index_store = FakeIndexStore()

    repository = EmbeddingRepository(
        embedding_service=embedding_service,
        index_store=index_store,
    )

    await repository.index_documents([])

    assert repository.documents == []

    assert embedding_service.embed_many_call_count == 0


@pytest.mark.asyncio
async def test_index_documents_embeds_title_and_content() -> None:
    document_a = KnowledgeDocument(
        id="asyncio",
        title="AsyncIO",
        content="Asynchronous programming in Python.",
        source="",
        updated_at=TEST_TIMESTAMP,
    )

    document_b = KnowledgeDocument(
        id="pydantic",
        title="Pydantic",
        content="Data validation using Python.",
        source="",
        updated_at=TEST_TIMESTAMP,
    )

    embedding_service = FakeEmbeddingService(
        embeddings=[
            [1.0, 0.0],
            [0.0, 1.0],
        ],
    )

    index_store = FakeIndexStore()

    repository = EmbeddingRepository(
        embedding_service=embedding_service,
        index_store=index_store,
    )

    await repository.index_documents([document_a, document_b])

    assert embedding_service.last_texts == [
        "AsyncIO\n\nAsynchronous programming in Python.",
        "Pydantic\n\nData validation using Python.",
    ]


@pytest.mark.asyncio
async def test_index_documents_rejects_embedding_count_mismatch() -> None:
    documents = [
        KnowledgeDocument(
            id="doc-1",
            title="Document 1",
            content="Content 1",
            source="",
            updated_at=TEST_TIMESTAMP,
        ),
        KnowledgeDocument(
            id="doc-2",
            title="Document 2",
            content="Content 2",
            source="",
            updated_at=TEST_TIMESTAMP,
        ),
        KnowledgeDocument(
            id="doc-3",
            title="Document 3",
            content="Content 3",
            source="",
            updated_at=TEST_TIMESTAMP,
        ),
    ]

    embedding_service = FakeEmbeddingService(
        embeddings=[
            [1.0, 0.0],
            [0.0, 1.0],
        ],
    )

    index_store = FakeIndexStore()

    repository = EmbeddingRepository(
        embedding_service=embedding_service,
        index_store=index_store,
    )

    with pytest.raises(
        ValueError,
        match="zip",
    ):
        await repository.index_documents(documents)


@pytest.mark.asyncio
async def test_index_documents_preserves_existing_index_when_embedding_fails() -> None:
    existing_document = KnowledgeDocument(
        id="existing",
        title="Existing",
        content="Existing content.",
        source="",
        updated_at=TEST_TIMESTAMP,
    )

    embedding_service = FakeEmbeddingService(
        embeddings=[
            [1.0, 0.0],
        ],
    )

    index_store = FakeIndexStore()

    repository = EmbeddingRepository(
        embedding_service=embedding_service,
        index_store=index_store,
    )

    await repository.index_documents([existing_document])

    old_index = repository.documents.copy()

    embedding_service.error = RuntimeError("Embedding service failed")

    new_document = KnowledgeDocument(
        id="new",
        title="New",
        content="New content.",
        source="",
        updated_at=TEST_TIMESTAMP,
    )

    with pytest.raises(
        RuntimeError,
        match="Embedding service failed",
    ):
        await repository.index_documents([new_document])

    assert repository.documents == old_index


@pytest.mark.asyncio
async def test_index_documents_saves_semantic_index() -> None:
    embedding_service = FakeEmbeddingService(
        embeddings=[
            [0.1, 0.2, 0.3],
            [0.4, 0.5, 0.6],
        ],
    )

    index_store = FakeIndexStore()

    repository = EmbeddingRepository(
        embedding_service=embedding_service,
        index_store=index_store,
    )

    documents = [
        KnowledgeDocument(
            id="asyncio",
            title="AsyncIO",
            content="Asynchronous programming in Python.",
            source="",
            updated_at=TEST_TIMESTAMP,
        ),
        KnowledgeDocument(
            id="pydantic",
            title="Pydantic",
            content="Data validation using Python.",
            source="",
            updated_at=TEST_TIMESTAMP,
        ),
    ]

    await repository.index_documents(documents)

    assert index_store.index is not None
    assert index_store.index.metadata == embedding_service.metadata
    assert index_store.index.documents == repository.documents


@pytest.mark.asyncio
async def test_load_index_restores_documents() -> None:
    embedding_service = FakeEmbeddingService(
        embeddings=[
            [0.1, 0.2, 0.3],
        ],
    )

    index_store = FakeIndexStore()

    repository = EmbeddingRepository(
        embedding_service=embedding_service,
        index_store=index_store,
    )

    documents = [
        KnowledgeDocument(
            id="asyncio",
            title="AsyncIO",
            content="Asynchronous programming in Python.",
            source="",
            updated_at=TEST_TIMESTAMP,
        ),
    ]

    await repository.index_documents(documents)

    repository.documents = []

    loaded = await repository.load_index()

    assert loaded is True
    assert len(repository.documents) == 1
    assert repository.documents[0].document.id == "asyncio"


@pytest.mark.asyncio
async def test_load_index_returns_false_when_index_does_not_exist() -> None:
    embedding_service = FakeEmbeddingService(
        embeddings=[],
    )

    index_store = FakeIndexStore()

    repository = EmbeddingRepository(
        embedding_service=embedding_service,
        index_store=index_store,
    )

    loaded = await repository.load_index()

    assert loaded is False
    assert repository.documents == []


@pytest.mark.asyncio
async def test_index_documents_does_not_update_memory_when_save_fails() -> None:
    embedding_service = FakeEmbeddingService(
        embeddings=[
            [0.1, 0.2, 0.3],
        ],
    )

    repository = EmbeddingRepository(
        embedding_service=embedding_service,
        index_store=FailingIndexStore(),
    )

    document = KnowledgeDocument(
        id="asyncio",
        title="AsyncIO",
        content="Asynchronous programming in Python.",
        source="",
        updated_at=TEST_TIMESTAMP,
    )

    with pytest.raises(RuntimeError):
        await repository.index_documents([document])

    assert repository.documents == []


async def test_get_stale_documents_includes_missing_documents() -> None:
    embedding_service = FakeEmbeddingService(
        embeddings=[],
    )

    repository = EmbeddingRepository(
        embedding_service=embedding_service,
        index_store=FakeIndexStore(),
    )

    document = KnowledgeDocument(
        id="asyncio",
        title="AsyncIO",
        content="Asynchronous programming in Python.",
        source="",
        updated_at=TEST_TIMESTAMP,
    )

    result = repository.get_stale_documents([document])

    assert result == [document]


async def test_get_stale_documents_detects_stale_embedding() -> None:
    embedding_service = FakeEmbeddingService(
        embeddings=[[0.1, 0.2, 0.3]],
    )

    repository = EmbeddingRepository(
        embedding_service=embedding_service,
        index_store=FakeIndexStore(),
    )

    document = KnowledgeDocument(
        id="asyncio",
        title="AsyncIO",
        content="Updated content.",
        source="",
        updated_at=datetime(2026, 8, 22, 10, 0, tzinfo=UTC),
    )

    embedded_document = EmbeddedDocument(
        document=document,
        embedding=[0.1, 0.2, 0.3],
        embedded_at=datetime(2026, 8, 22, 9, 0, tzinfo=UTC),
    )

    repository.documents = [embedded_document]

    result = repository.get_stale_documents([document])

    assert result == [document]


async def test_get_stale_documents_accepts_matching_timestamp() -> None:
    timestamp = datetime(2026, 8, 22, 10, 0, tzinfo=UTC)

    document = KnowledgeDocument(
        id="asyncio",
        title="AsyncIO",
        content="Asynchronous programming in Python.",
        source="",
        updated_at=timestamp,
    )

    embedded_document = EmbeddedDocument(
        document=document,
        embedding=[0.1, 0.2, 0.3],
        embedded_at=timestamp,
    )

    repository = EmbeddingRepository(
        embedding_service=FakeEmbeddingService(
            embeddings=[],
        ),
        index_store=FakeIndexStore(),
    )

    repository.documents = [embedded_document]

    result = repository.get_stale_documents([document])

    assert result == []


@pytest.mark.asyncio
async def test_sync_documents_does_not_save_when_index_is_current() -> None:
    timestamp = datetime(
        2026,
        8,
        22,
        10,
        0,
        tzinfo=UTC,
    )

    document_a = KnowledgeDocument(
        id="a",
        title="A",
        content="Document A",
        source="",
        updated_at=timestamp,
    )

    document_b = KnowledgeDocument(
        id="b",
        title="B",
        content="Document B",
        source="",
        updated_at=timestamp,
    )

    embedding_service = FakeEmbeddingService(
        embeddings=[],
    )

    index_store = FakeIndexStore()

    repository = EmbeddingRepository(
        embedding_service=embedding_service,
        index_store=index_store,
    )

    repository.documents = [
        EmbeddedDocument(
            document=document_a,
            embedding=[1.0, 0.0, 0.0],
            embedded_at=timestamp,
        ),
        EmbeddedDocument(
            document=document_b,
            embedding=[0.0, 1.0, 0.0],
            embedded_at=timestamp,
        ),
    ]

    await repository.sync_documents([document_a, document_b])

    assert embedding_service.embed_many_call_count == 0
    assert index_store.save_calls == 0


@pytest.mark.asyncio
async def test_sync_documents_saves_when_document_is_new() -> None:
    timestamp = datetime(
        2026,
        8,
        22,
        10,
        0,
        tzinfo=UTC,
    )

    document_a = KnowledgeDocument(
        id="a",
        title="A",
        content="Document A",
        source="",
        updated_at=timestamp,
    )

    document_b = KnowledgeDocument(
        id="b",
        title="B",
        content="Document B",
        source="",
        updated_at=timestamp,
    )

    embedding_service = FakeEmbeddingService(
        embeddings=[[0.0, 0.0, 1.0]],
    )

    index_store = FakeIndexStore()

    repository = EmbeddingRepository(
        embedding_service=embedding_service,
        index_store=index_store,
    )

    repository.documents = [
        EmbeddedDocument(
            document=document_a,
            embedding=[1.0, 0.0, 0.0],
            embedded_at=timestamp,
        ),
    ]

    await repository.sync_documents([document_a, document_b])

    assert index_store.save_calls >= 1

    assert [doc.document.id for doc in repository.documents] == [
        "a",
        "b",
    ]


@pytest.mark.asyncio
async def test_sync_documents_saves_when_document_is_deleted() -> None:
    timestamp = datetime(
        2026,
        8,
        22,
        10,
        0,
        tzinfo=UTC,
    )

    document_a = KnowledgeDocument(
        id="a",
        title="A",
        content="Document A",
        source="",
        updated_at=timestamp,
    )

    document_b = KnowledgeDocument(
        id="b",
        title="B",
        content="Document B",
        source="",
        updated_at=timestamp,
    )

    document_c = KnowledgeDocument(
        id="c",
        title="C",
        content="Document C",
        source="",
        updated_at=timestamp,
    )

    embedding_service = FakeEmbeddingService(
        embeddings=[],
    )

    index_store = FakeIndexStore()

    repository = EmbeddingRepository(
        embedding_service=embedding_service,
        index_store=index_store,
    )

    repository.documents = [
        EmbeddedDocument(
            document=document_a,
            embedding=[1.0, 0.0, 0.0],
            embedded_at=timestamp,
        ),
        EmbeddedDocument(
            document=document_b,
            embedding=[0.0, 1.0, 0.0],
            embedded_at=timestamp,
        ),
        EmbeddedDocument(
            document=document_c,
            embedding=[0.0, 0.0, 1.0],
            embedded_at=timestamp,
        ),
    ]

    await repository.sync_documents([document_a, document_b])

    assert embedding_service.embed_many_call_count == 0
    assert index_store.save_calls >= 1

    assert [document.document.id for document in repository.documents] == [
        "a",
        "b",
    ]
