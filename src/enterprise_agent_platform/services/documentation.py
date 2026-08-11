from enterprise_agent_platform.models.search_result import SearchResult
from enterprise_agent_platform.models.search_results import SearchResults


class DocumentationService:
    """Provides access to project documentation."""

    def search(
        self,
        query: str,
    ) -> SearchResults:
        return SearchResults(
            results=[
                SearchResult(
                    title="AsyncIO",
                    url="https://docs.python.org/3/library/asyncio.html",
                    snippet=f"Dummy result for '{query}'.",
                )
            ]
        )
