from enterprise_agent_platform.models.memory import Memory


class InMemoryMemoryStore:
    def __init__(self) -> None:
        self._memories: dict[tuple[str, str], Memory] = {}

    async def save(self, memory: Memory) -> None:
        self._memories[(memory.user_id, memory.key)] = memory

    async def get(
        self,
        user_id: str,
        key: str,
    ) -> Memory | None:
        return self._memories.get((user_id, key))

    async def delete(
        self,
        user_id: str,
        key: str,
    ) -> None:
        self._memories.pop((user_id, key), None)
