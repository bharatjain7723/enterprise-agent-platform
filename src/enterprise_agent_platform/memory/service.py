from enterprise_agent_platform.memory.repository import MemoryRepository
from enterprise_agent_platform.models.memory import Memory


class MemoryService:
    """Provides application-level memory capabilities."""

    def __init__(self, repository: MemoryRepository) -> None:
        self.repository = repository

    async def remember(
        self,
        user_id: str,
        key: str,
        value: str,
    ) -> Memory:
        return await self.repository.save(
            user_id=user_id,
            key=key,
            value=value,
        )

    async def recall(
        self,
        user_id: str,
        key: str,
    ) -> Memory | None:
        return await self.repository.get(
            user_id=user_id,
            key=key,
        )

    async def forget(
        self,
        user_id: str,
        key: str,
    ) -> None:
        await self.repository.delete(
            user_id=user_id,
            key=key,
        )
