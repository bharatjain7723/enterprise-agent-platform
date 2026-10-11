from typing import Protocol

from enterprise_agent_platform.models.memory import Memory


class MemoryStore(Protocol):
    async def save(self, memory: Memory) -> None: ...

    async def get(
        self,
        user_id: str,
        key: str,
    ) -> Memory | None: ...

    async def delete(
        self,
        user_id: str,
        key: str,
    ) -> None: ...
