from typing import Protocol

from enterprise_agent_platform.models.search_results import SearchResults


class DocumentationSearcher(Protocol):
    """Contract implemented by documentation search services."""

    def search(
        self,
        query: str,
    ) -> SearchResults: ...
