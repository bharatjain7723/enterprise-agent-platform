import pytest

from enterprise_agent_platform.memory.in_memory_store import (
    InMemoryMemoryStore,
)
from enterprise_agent_platform.memory.repository import MemoryRepository
from enterprise_agent_platform.memory.service import MemoryService


@pytest.fixture
def service() -> MemoryService:
    store = InMemoryMemoryStore()
    repository = MemoryRepository(store)
    return MemoryService(repository)


@pytest.mark.asyncio
async def test_remember_creates_memory(
    service: MemoryService,
) -> None:
    memory = await service.remember(
        user_id="user-1",
        key="preferred_language",
        value="Python",
    )

    assert memory.user_id == "user-1"
    assert memory.key == "preferred_language"
    assert memory.value == "Python"
    assert memory.id


@pytest.mark.asyncio
async def test_recall_returns_existing_memory(
    service: MemoryService,
) -> None:
    created = await service.remember(
        user_id="user-1",
        key="preferred_language",
        value="Python",
    )

    result = await service.recall(
        user_id="user-1",
        key="preferred_language",
    )

    assert result == created


@pytest.mark.asyncio
async def test_recall_missing_memory_returns_none(
    service: MemoryService,
) -> None:
    result = await service.recall(
        user_id="user-1",
        key="preferred_language",
    )

    assert result is None


@pytest.mark.asyncio
async def test_remember_updates_existing_memory(
    service: MemoryService,
) -> None:
    original = await service.remember(
        user_id="user-1",
        key="preferred_language",
        value="Python",
    )

    updated = await service.remember(
        user_id="user-1",
        key="preferred_language",
        value="TypeScript",
    )

    assert updated.id == original.id
    assert updated.value == "TypeScript"


@pytest.mark.asyncio
async def test_memories_are_isolated_by_user(
    service: MemoryService,
) -> None:
    user_one = await service.remember(
        user_id="user-1",
        key="preferred_language",
        value="Python",
    )

    user_two = await service.remember(
        user_id="user-2",
        key="preferred_language",
        value="Java",
    )

    result_one = await service.recall(
        user_id="user-1",
        key="preferred_language",
    )
    result_two = await service.recall(
        user_id="user-2",
        key="preferred_language",
    )

    assert result_one == user_one
    assert result_two == user_two


@pytest.mark.asyncio
async def test_forget_removes_existing_memory(
    service: MemoryService,
) -> None:
    await service.remember(
        user_id="user-1",
        key="preferred_language",
        value="Python",
    )

    await service.forget(
        user_id="user-1",
        key="preferred_language",
    )

    result = await service.recall(
        user_id="user-1",
        key="preferred_language",
    )

    assert result is None


@pytest.mark.asyncio
async def test_forget_missing_memory_is_noop(
    service: MemoryService,
) -> None:
    await service.forget(
        user_id="user-1",
        key="preferred_language",
    )

    result = await service.recall(
        user_id="user-1",
        key="preferred_language",
    )

    assert result is None


@pytest.mark.asyncio
async def test_same_user_can_have_multiple_memories(
    service: MemoryService,
) -> None:
    language = await service.remember(
        user_id="user-1",
        key="preferred_language",
        value="Python",
    )

    framework = await service.remember(
        user_id="user-1",
        key="preferred_framework",
        value="React",
    )

    assert (
        await service.recall(
            user_id="user-1",
            key="preferred_language",
        )
    ) == language

    assert (
        await service.recall(
            user_id="user-1",
            key="preferred_framework",
        )
    ) == framework
