from enterprise_agent_platform.models.knowledge_search_result import KnowledgeSearchResult
from enterprise_agent_platform.services.protocols import DocumentationSearcher


class DocumentationService:
    """Provides access to project documentation."""

    def __init__(
        self,
        searcher: DocumentationSearcher,
    ) -> None:
        self.searcher = searcher

    async def search(
        self,
        query: str,
    ) -> list[KnowledgeSearchResult]:
        return await self.searcher.search(query)
