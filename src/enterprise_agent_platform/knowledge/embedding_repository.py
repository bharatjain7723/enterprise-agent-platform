from datetime import UTC, datetime

from enterprise_agent_platform.knowledge.similarity import cosine_similarity
from enterprise_agent_platform.models.embedded_document import EmbeddedDocument
from enterprise_agent_platform.models.knowledge_document import KnowledgeDocument
from enterprise_agent_platform.models.knowledge_search_result import KnowledgeSearchResult
from enterprise_agent_platform.models.semantic_index import SemanticIndex
from enterprise_agent_platform.services.protocols import (
    EmbeddingService,
    IndexStore,
)


class EmbeddingRepository:
    def __init__(
        self,
        embedding_service: EmbeddingService,
        index_store: IndexStore,
    ):
        self.documents: list[EmbeddedDocument] = []
        self.embedding_service = embedding_service
        self.index_store = index_store

    async def index_documents(
        self,
        documents: list[KnowledgeDocument],
    ) -> None:
        if not documents:
            return

        texts = [self._document_text(document) for document in documents]

        embeddings = await self.embedding_service.embed_many(texts)

        embedded_at = datetime.now(UTC)

        embedded_documents = [
            EmbeddedDocument(document=document, embedding=embedding, embedded_at=embedded_at)
            for document, embedding in zip(
                documents,
                embeddings,
                strict=True,
            )
        ]

        existing_by_id = {item.document.id: item for item in self.documents}

        for embedded_document in embedded_documents:
            existing_by_id[embedded_document.document.id] = embedded_document

        current_embedded_documents = list(existing_by_id.values())

        index = SemanticIndex(
            metadata=self.embedding_service.metadata,
            documents=current_embedded_documents,
        )

        await self.index_store.save(index)

        self.documents = current_embedded_documents

    async def load_index(self) -> bool:
        index = await self.index_store.load()

        if index is None:
            return False

        self.documents = index.documents

        return True

    async def search(
        self,
        query: str,
    ) -> list[KnowledgeSearchResult]:
        if not query.strip():
            raise ValueError("Query cannot be empty.")

        if not self.documents:
            return []

        query_embedding = await self.embedding_service.embed(query)

        results: list[KnowledgeSearchResult] = []

        for embedded_document in self.documents:
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

        return results

    def _document_text(
        self,
        document: KnowledgeDocument,
    ) -> str:
        return f"{document.title}\n\n{document.content}"

    def get_stale_documents(
        self,
        documents: list[KnowledgeDocument],
    ) -> list[KnowledgeDocument]:
        embedded_by_id = {item.document.id: item for item in self.documents}

        stale_documents: list[KnowledgeDocument] = []

        for document in documents:
            embedded = embedded_by_id.get(document.id)

            if embedded is None:
                stale_documents.append(document)
                continue

            if embedded.embedded_at < document.updated_at:
                stale_documents.append(document)

        return stale_documents

    def _create_index(self) -> SemanticIndex:
        return SemanticIndex(
            documents=self.documents,
            metadata=self.embedding_service.metadata,
        )

    async def sync_documents(
        self,
        documents: list[KnowledgeDocument],
    ) -> None:
        stale_documents = self.get_stale_documents(documents)

        previous_ids = {embedded.document.id for embedded in self.documents}

        source_ids = {document.id for document in documents}

        deleted_ids = previous_ids - source_ids

        if stale_documents:
            await self.index_documents(stale_documents)

        embedded_by_id = {
            embedded.document.id: embedded
            for embedded in self.documents
            if embedded.document.id in source_ids
        }

        self.documents = list(embedded_by_id.values())

        changed = bool(stale_documents or deleted_ids)

        if changed:
            await self.index_store.save(self._create_index())
