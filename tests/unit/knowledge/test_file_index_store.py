import json
from datetime import UTC, datetime
from pathlib import Path

import pytest
from pydantic import ValidationError

from enterprise_agent_platform.knowledge.file_index_store import FileIndexStore
from enterprise_agent_platform.models.embedded_document import EmbeddedDocument
from enterprise_agent_platform.models.embedding_metadata import EmbeddingMetadata
from enterprise_agent_platform.models.knowledge_document import KnowledgeDocument
from enterprise_agent_platform.models.semantic_index import SemanticIndex

TEST_TIMESTAMP = datetime(
    2026,
    8,
    22,
    10,
    0,
    tzinfo=UTC,
)


def create_index() -> SemanticIndex:
    document = KnowledgeDocument(
        id="asyncio",
        title="AsyncIO",
        content="Asynchronous programming in Python.",
        source="",
        updated_at=TEST_TIMESTAMP,
    )

    embedded_document = EmbeddedDocument(
        document=document,
        embedding=[0.1, 0.2, 0.3],
        embedded_at=TEST_TIMESTAMP,
    )

    metadata = EmbeddingMetadata(
        provider="openai",
        model="text-embedding-3-small",
        dimensions=3,
        index_version=1,
    )

    return SemanticIndex(
        metadata=metadata,
        documents=[embedded_document],
    )


@pytest.mark.asyncio
async def test_load_returns_none_when_file_does_not_exist(
    tmp_path: Path,
) -> None:
    path = tmp_path / "index.json"

    store = FileIndexStore(path)

    result = await store.load()

    assert result is None


@pytest.mark.asyncio
async def test_save_creates_file(
    tmp_path: Path,
) -> None:
    path = tmp_path / "index.json"

    store = FileIndexStore(path)

    await store.save(create_index())

    assert path.exists()


@pytest.mark.asyncio
async def test_save_and_load_round_trip(
    tmp_path: Path,
) -> None:
    path = tmp_path / "index.json"

    store = FileIndexStore(path)

    index = create_index()

    await store.save(index)

    loaded = await store.load()

    assert loaded == index


@pytest.mark.asyncio
async def test_save_creates_parent_directories(
    tmp_path: Path,
) -> None:
    path = tmp_path / "nested" / "indexes" / "index.json"

    store = FileIndexStore(path)

    await store.save(create_index())

    assert path.exists()


@pytest.mark.asyncio
async def test_load_raises_for_invalid_json(
    tmp_path: Path,
) -> None:
    path = tmp_path / "index.json"

    path.write_text(
        "{invalid json",
        encoding="utf-8",
    )

    store = FileIndexStore(path)

    with pytest.raises(json.JSONDecodeError):
        await store.load()


@pytest.mark.asyncio
async def test_load_raises_for_invalid_index_data(
    tmp_path: Path,
) -> None:
    path = tmp_path / "index.json"

    path.write_text(
        json.dumps(
            {
                "metadata": {
                    "provider": "openai",
                },
                "documents": [],
            }
        ),
        encoding="utf-8",
    )

    store = FileIndexStore(path)

    with pytest.raises(ValidationError):
        await store.load()
