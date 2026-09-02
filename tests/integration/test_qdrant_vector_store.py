from collections.abc import AsyncGenerator
from datetime import UTC, datetime

import pytest
import pytest_asyncio
from qdrant_client import AsyncQdrantClient

from enterprise_agent_platform.knowledge.qdrant_vector_store import (
    QdrantVectorStore,
)
from enterprise_agent_platform.models.embedded_document import EmbeddedDocument
from enterprise_agent_platform.models.knowledge_document import KnowledgeDocument


def create_embedded_document(
    document_id: str,
    title: str,
    embedding: list[float],
) -> EmbeddedDocument:
    updated_at = datetime.now(UTC)
    embedded_at = datetime.now(UTC)

    document = KnowledgeDocument(
        id=document_id,
        title=title,
        content=f"Content for {title}.",
        source=f"{document_id}.md",
        updated_at=updated_at,
    )

    return EmbeddedDocument(
        document=document,
        embedding=embedding,
        embedded_at=embedded_at,
    )


@pytest_asyncio.fixture
async def vector_store() -> AsyncGenerator[QdrantVectorStore, None]:
    client = AsyncQdrantClient(
        location=":memory:",
    )

    store = QdrantVectorStore(
        client=client,
        collection_name="test_documents",
        dimensions=2,
    )

    await store.initialize()

    yield store

    await client.close()


@pytest.mark.asyncio
async def test_upsert_many_and_search(
    vector_store: QdrantVectorStore,
) -> None:
    first = create_embedded_document(
        document_id="first",
        title="First",
        embedding=[1.0, 0.0],
    )

    second = create_embedded_document(
        document_id="second",
        title="Second",
        embedding=[0.0, 1.0],
    )

    await vector_store.upsert_many([first, second])

    results = await vector_store.search(
        query_embedding=[1.0, 0.0],
    )

    assert len(results) == 2
    assert results[0].document.id == "first"
    assert results[1].document.id == "second"
    assert results[0].score > results[1].score


@pytest.mark.asyncio
async def test_upsert_replaces_existing_document(
    vector_store: QdrantVectorStore,
) -> None:
    original = create_embedded_document(
        document_id="doc-1",
        title="Original",
        embedding=[1.0, 0.0],
    )

    updated = create_embedded_document(
        document_id="doc-1",
        title="Updated",
        embedding=[0.0, 1.0],
    )

    await vector_store.upsert_many([original])
    await vector_store.upsert_many([updated])

    results = await vector_store.search(
        query_embedding=[0.0, 1.0],
    )

    assert len(results) == 1
    assert results[0].document.id == "doc-1"
    assert results[0].document.title == "Updated"


@pytest.mark.asyncio
async def test_delete_removes_document(
    vector_store: QdrantVectorStore,
) -> None:
    document = create_embedded_document(
        document_id="doc-1",
        title="Document",
        embedding=[1.0, 0.0],
    )

    await vector_store.upsert_many([document])

    await vector_store.delete("doc-1")

    results = await vector_store.search(
        query_embedding=[1.0, 0.0],
    )

    assert results == []


@pytest.mark.asyncio
async def test_search_respects_limit(
    vector_store: QdrantVectorStore,
) -> None:
    documents = [
        create_embedded_document(
            document_id="doc-1",
            title="Document 1",
            embedding=[1.0, 0.0],
        ),
        create_embedded_document(
            document_id="doc-2",
            title="Document 2",
            embedding=[0.9, 0.1],
        ),
        create_embedded_document(
            document_id="doc-3",
            title="Document 3",
            embedding=[0.0, 1.0],
        ),
    ]

    await vector_store.upsert_many(documents)

    results = await vector_store.search(
        query_embedding=[1.0, 0.0],
        limit=2,
    )

    assert len(results) == 2
    assert results[0].document.id == "doc-1"
    assert results[1].document.id == "doc-2"


@pytest.mark.asyncio
async def test_payload_metadata_survives_round_trip(
    vector_store: QdrantVectorStore,
) -> None:
    document = create_embedded_document(
        document_id="asyncio",
        title="AsyncIO",
        embedding=[1.0, 0.0],
    )

    await vector_store.upsert_many([document])

    results = await vector_store.search(
        query_embedding=[1.0, 0.0],
    )

    assert len(results) == 1

    result = results[0]

    assert result.document.id == document.document.id
    assert result.document.title == document.document.title
    assert result.document.content == document.document.content
    assert result.document.source == document.document.source
    assert result.document.updated_at == document.document.updated_at


@pytest.mark.asyncio
async def test_search_rejects_non_positive_limit(
    vector_store: QdrantVectorStore,
) -> None:
    with pytest.raises(
        ValueError,
        match="Limit must be greater than zero.",
    ):
        await vector_store.search(
            query_embedding=[1.0, 0.0],
            limit=0,
        )


@pytest.mark.asyncio
async def test_initialize_is_idempotent(
    vector_store: QdrantVectorStore,
) -> None:
    await vector_store.initialize()
    await vector_store.initialize()

    results = await vector_store.search(
        query_embedding=[1.0, 0.0],
    )

    assert results == []


@pytest.mark.asyncio
async def test_upsert_many_with_empty_list_is_noop(
    vector_store: QdrantVectorStore,
) -> None:
    await vector_store.upsert_many([])

    results = await vector_store.search(
        query_embedding=[1.0, 0.0],
    )

    assert results == []


@pytest.mark.asyncio
async def test_delete_nonexistent_document_is_noop(
    vector_store: QdrantVectorStore,
) -> None:
    await vector_store.delete("does-not-exist")

    results = await vector_store.search(
        query_embedding=[1.0, 0.0],
    )

    assert results == []
