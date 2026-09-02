from enterprise_agent_platform.knowledge.similarity import cosine_similarity
from enterprise_agent_platform.models.embedded_document import EmbeddedDocument
from enterprise_agent_platform.models.knowledge_search_result import (
    KnowledgeSearchResult,
)


class InMemoryVectorStore:
    """Stores embedded documents in memory and performs vector search."""

    def __init__(self) -> None:
        self.documents: dict[str, EmbeddedDocument] = {}

    async def upsert_many(
        self,
        documents: list[EmbeddedDocument],
    ) -> None:
        for document in documents:
            self.documents[document.document.id] = document

    async def delete(
        self,
        document_id: str,
    ) -> None:
        self.documents.pop(document_id, None)

    async def search(
        self,
        query_embedding: list[float],
        limit: int = 5,
    ) -> list[KnowledgeSearchResult]:
        if limit <= 0:
            raise ValueError("Limit must be greater than zero.")

        results: list[KnowledgeSearchResult] = []

        for embedded_document in self.documents.values():
            score = cosine_similarity(
                query_embedding,
                embedded_document.embedding,
            )

            results.append(
                KnowledgeSearchResult(
                    document=embedded_document.document,
                    score=score,
                    snippet="",
                )
            )

        results.sort(
            key=lambda result: result.score,
            reverse=True,
        )

        return results[:limit]
