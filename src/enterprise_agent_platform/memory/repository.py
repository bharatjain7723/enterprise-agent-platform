from datetime import UTC, datetime
from uuid import uuid4

from enterprise_agent_platform.memory.protocols import MemoryStore
from enterprise_agent_platform.models.memory import Memory


class MemoryRepository:
    def __init__(self, store: MemoryStore) -> None:
        self.store = store

    async def save(
        self,
        user_id: str,
        key: str,
        value: str,
    ) -> Memory:
        now = datetime.now(UTC)

        existing = await self.store.get(
            user_id=user_id,
            key=key,
        )

        memory = Memory(
            id=existing.id if existing is not None else str(uuid4()),
            user_id=user_id,
            key=key,
            value=value,
            created_at=(existing.created_at if existing is not None else now),
            updated_at=now,
        )

        await self.store.save(memory)

        return memory

    async def get(
        self,
        user_id: str,
        key: str,
    ) -> Memory | None:
        return await self.store.get(
            user_id=user_id,
            key=key,
        )

    async def delete(
        self,
        user_id: str,
        key: str,
    ) -> None:
        await self.store.delete(
            user_id=user_id,
            key=key,
        )
