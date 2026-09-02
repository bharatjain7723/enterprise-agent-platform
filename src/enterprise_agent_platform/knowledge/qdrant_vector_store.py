from datetime import datetime
from uuid import NAMESPACE_URL, uuid5

from qdrant_client import AsyncQdrantClient, models

from enterprise_agent_platform.models.embedded_document import EmbeddedDocument
from enterprise_agent_platform.models.knowledge_search_result import (
    KnowledgeSearchResult,
)


class QdrantVectorStore:
    """Stores and searches embedded documents using Qdrant."""

    def __init__(
        self,
        client: AsyncQdrantClient,
        collection_name: str,
        dimensions: int,
    ) -> None:
        self.client = client
        self.collection_name = collection_name
        self.dimensions = dimensions

    async def initialize(self) -> None:
        collections = await self.client.get_collections()

        if any(collection.name == self.collection_name for collection in collections.collections):
            return

        await self.client.create_collection(
            collection_name=self.collection_name,
            vectors_config=models.VectorParams(
                size=self.dimensions,
                distance=models.Distance.COSINE,
            ),
        )

    async def upsert_many(
        self,
        documents: list[EmbeddedDocument],
    ) -> None:
        if not documents:
            return

        points = [
            models.PointStruct(
                id=str(
                    uuid5(
                        NAMESPACE_URL,
                        document.document.id,
                    )
                ),
                vector=document.embedding,
                payload={
                    "document_id": document.document.id,
                    "title": document.document.title,
                    "content": document.document.content,
                    "source": document.document.source,
                    "updated_at": document.document.updated_at.isoformat(),
                    "embedded_at": document.embedded_at.isoformat(),
                },
            )
            for document in documents
        ]

        await self.client.upsert(
            collection_name=self.collection_name,
            points=points,
        )

    async def delete(
        self,
        document_id: str,
    ) -> None:
        await self.client.delete(
            collection_name=self.collection_name,
            points_selector=models.PointIdsList(
                points=[
                    str(
                        uuid5(
                            NAMESPACE_URL,
                            document_id,
                        )
                    )
                ],
            ),
        )

    async def search(
        self,
        query_embedding: list[float],
        limit: int = 5,
    ) -> list[KnowledgeSearchResult]:
        if limit <= 0:
            raise ValueError("Limit must be greater than zero.")

        results = await self.client.query_points(
            collection_name=self.collection_name,
            query=query_embedding,
            limit=limit,
            with_payload=True,
        )

        search_results: list[KnowledgeSearchResult] = []

        for result in results.points:
            payload = result.payload

            if payload is None:
                continue

            document = self._document_from_payload(payload)

            search_results.append(
                KnowledgeSearchResult(
                    document=document,
                    score=result.score,
                    snippet="",
                )
            )

        return search_results

    def _document_from_payload(
        self,
        payload: dict[str, object],
    ):
        from enterprise_agent_platform.models.knowledge_document import (
            KnowledgeDocument,
        )

        return KnowledgeDocument(
            id=str(payload["document_id"]),
            title=str(payload["title"]),
            content=str(payload["content"]),
            source=str(payload["source"]),
            updated_at=datetime.fromisoformat(str(payload["updated_at"])),
        )
