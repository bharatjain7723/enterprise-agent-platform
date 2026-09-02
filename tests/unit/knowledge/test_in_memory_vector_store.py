from datetime import UTC, datetime

import pytest

from enterprise_agent_platform.knowledge.in_memory_vector_store import (
    InMemoryVectorStore,
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


@pytest.mark.asyncio
async def test_upsert_many_and_search() -> None:
    store = InMemoryVectorStore()

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

    await store.upsert_many([first, second])

    results = await store.search(
        query_embedding=[1.0, 0.0],
    )

    assert len(results) == 2
    assert results[0].document.id == "first"
    assert results[1].document.id == "second"
    assert results[0].score > results[1].score


@pytest.mark.asyncio
async def test_upsert_many_replaces_existing_document() -> None:
    store = InMemoryVectorStore()

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

    await store.upsert_many([original])
    await store.upsert_many([updated])

    assert len(store.documents) == 1
    assert store.documents["doc-1"].document.title == "Updated"
    assert store.documents["doc-1"].embedding == [0.0, 1.0]


@pytest.mark.asyncio
async def test_delete_removes_document() -> None:
    store = InMemoryVectorStore()

    document = create_embedded_document(
        document_id="doc-1",
        title="Document",
        embedding=[1.0, 0.0],
    )

    await store.upsert_many([document])

    await store.delete("doc-1")

    results = await store.search(
        query_embedding=[1.0, 0.0],
    )

    assert results == []
    assert "doc-1" not in store.documents


@pytest.mark.asyncio
async def test_delete_nonexistent_document_does_nothing() -> None:
    store = InMemoryVectorStore()

    await store.delete("does-not-exist")

    assert store.documents == {}


@pytest.mark.asyncio
async def test_search_respects_limit() -> None:
    store = InMemoryVectorStore()

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

    await store.upsert_many(documents)

    results = await store.search(
        query_embedding=[1.0, 0.0],
        limit=2,
    )

    assert len(results) == 2
    assert results[0].document.id == "doc-1"
    assert results[1].document.id == "doc-2"


@pytest.mark.asyncio
async def test_search_rejects_zero_limit() -> None:
    store = InMemoryVectorStore()

    with pytest.raises(
        ValueError,
        match="Limit must be greater than zero.",
    ):
        await store.search(
            query_embedding=[1.0, 0.0],
            limit=0,
        )


@pytest.mark.asyncio
async def test_search_rejects_negative_limit() -> None:
    store = InMemoryVectorStore()

    with pytest.raises(
        ValueError,
        match="Limit must be greater than zero.",
    ):
        await store.search(
            query_embedding=[1.0, 0.0],
            limit=-1,
        )
