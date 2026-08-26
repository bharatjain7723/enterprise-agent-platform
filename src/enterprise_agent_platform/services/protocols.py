from typing import Protocol

from enterprise_agent_platform.models.embedding_metadata import EmbeddingMetadata
from enterprise_agent_platform.models.knowledge_search_result import KnowledgeSearchResult
from enterprise_agent_platform.models.semantic_index import SemanticIndex


class DocumentationSearcher(Protocol):
    """Contract implemented by documentation search services."""

    async def search(
        self,
        query: str,
    ) -> list[KnowledgeSearchResult]: ...


class EmbeddingService(Protocol):
    @property
    def metadata(self) -> EmbeddingMetadata: ...

    async def embed(
        self,
        text: str,
    ) -> list[float]: ...

    async def embed_many(
        self,
        texts: list[str],
    ) -> list[list[float]]: ...


class IndexStore(Protocol):
    async def save(
        self,
        index: SemanticIndex,
    ) -> None: ...

    async def load(self) -> SemanticIndex | None: ...
