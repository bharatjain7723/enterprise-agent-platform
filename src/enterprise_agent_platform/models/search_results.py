from pydantic import BaseModel, Field

from enterprise_agent_platform.models.search_result import SearchResult


class SearchResults(BaseModel):
    results: list[SearchResult] = Field(
        default_factory=lambda: [],
        description="Search results",
    )
