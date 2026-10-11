from datetime import UTC

import pytest

from enterprise_agent_platform.memory.in_memory_store import (
    InMemoryMemoryStore,
)
from enterprise_agent_platform.memory.repository import MemoryRepository


@pytest.fixture
def store() -> InMemoryMemoryStore:
    return InMemoryMemoryStore()


@pytest.fixture
def repository(
    store: InMemoryMemoryStore,
) -> MemoryRepository:
    return MemoryRepository(store)


@pytest.mark.asyncio
async def test_save_creates_new_memory(
    repository: MemoryRepository,
) -> None:
    memory = await repository.save(
        user_id="user-1",
        key="preferred_language",
        value="Python",
    )

    assert memory.user_id == "user-1"
    assert memory.key == "preferred_language"
    assert memory.value == "Python"
    assert memory.id
    assert memory.created_at.tzinfo == UTC
    assert memory.updated_at.tzinfo == UTC


@pytest.mark.asyncio
async def test_save_persists_memory(
    repository: MemoryRepository,
) -> None:
    memory = await repository.save(
        user_id="user-1",
        key="preferred_language",
        value="Python",
    )

    result = await repository.get(
        user_id="user-1",
        key="preferred_language",
    )

    assert result == memory


@pytest.mark.asyncio
async def test_get_missing_memory_returns_none(
    repository: MemoryRepository,
) -> None:
    result = await repository.get(
        user_id="user-1",
        key="preferred_language",
    )

    assert result is None


@pytest.mark.asyncio
async def test_save_existing_memory_updates_value(
    repository: MemoryRepository,
) -> None:
    original = await repository.save(
        user_id="user-1",
        key="preferred_language",
        value="Python",
    )

    updated = await repository.save(
        user_id="user-1",
        key="preferred_language",
        value="TypeScript",
    )

    assert updated.id == original.id
    assert updated.value == "TypeScript"


@pytest.mark.asyncio
async def test_save_existing_memory_preserves_created_at(
    repository: MemoryRepository,
) -> None:
    original = await repository.save(
        user_id="user-1",
        key="preferred_language",
        value="Python",
    )

    updated = await repository.save(
        user_id="user-1",
        key="preferred_language",
        value="TypeScript",
    )

    assert updated.created_at == original.created_at


@pytest.mark.asyncio
async def test_save_existing_memory_updates_updated_at(
    repository: MemoryRepository,
) -> None:
    original = await repository.save(
        user_id="user-1",
        key="preferred_language",
        value="Python",
    )

    updated = await repository.save(
        user_id="user-1",
        key="preferred_language",
        value="TypeScript",
    )

    assert updated.updated_at >= original.updated_at


@pytest.mark.asyncio
async def test_different_users_can_have_same_key(
    repository: MemoryRepository,
) -> None:
    user_one = await repository.save(
        user_id="user-1",
        key="preferred_language",
        value="Python",
    )

    user_two = await repository.save(
        user_id="user-2",
        key="preferred_language",
        value="Java",
    )

    assert user_one.id != user_two.id

    result_one = await repository.get(
        user_id="user-1",
        key="preferred_language",
    )
    result_two = await repository.get(
        user_id="user-2",
        key="preferred_language",
    )

    assert result_one == user_one
    assert result_two == user_two


@pytest.mark.asyncio
async def test_same_user_can_have_different_keys(
    repository: MemoryRepository,
) -> None:
    language = await repository.save(
        user_id="user-1",
        key="preferred_language",
        value="Python",
    )

    framework = await repository.save(
        user_id="user-1",
        key="preferred_framework",
        value="React",
    )

    assert language.id != framework.id

    result_language = await repository.get(
        user_id="user-1",
        key="preferred_language",
    )
    result_framework = await repository.get(
        user_id="user-1",
        key="preferred_framework",
    )

    assert result_language == language
    assert result_framework == framework


@pytest.mark.asyncio
async def test_delete_existing_memory(
    repository: MemoryRepository,
) -> None:
    await repository.save(
        user_id="user-1",
        key="preferred_language",
        value="Python",
    )

    await repository.delete(
        user_id="user-1",
        key="preferred_language",
    )

    result = await repository.get(
        user_id="user-1",
        key="preferred_language",
    )

    assert result is None


@pytest.mark.asyncio
async def test_delete_missing_memory_is_noop(
    repository: MemoryRepository,
) -> None:
    await repository.delete(
        user_id="user-1",
        key="preferred_language",
    )

    result = await repository.get(
        user_id="user-1",
        key="preferred_language",
    )

    assert result is None
