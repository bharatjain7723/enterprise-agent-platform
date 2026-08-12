from typing import Protocol

from enterprise_agent_platform.models.knowledge_search_result import (
    KnowledgeSearchResult,
)


class KnowledgeRepository(Protocol):
    """Provides access to knowledge documents."""

    def search(
        self,
        query: str,
    ) -> list[KnowledgeSearchResult]: ...
