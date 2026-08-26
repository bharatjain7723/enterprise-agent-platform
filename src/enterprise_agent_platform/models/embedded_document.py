from datetime import datetime

from pydantic import BaseModel, Field

from enterprise_agent_platform.models.knowledge_document import (
    KnowledgeDocument,
)


class EmbeddedDocument(BaseModel):
    """A knowledge document together with its embedding."""

    document: KnowledgeDocument = Field(description="Original document.")

    embedding: list[float] = Field(default_factory=lambda: [], description="Embedding vector.")

    embedded_at: datetime = Field(description="time of embedding the document")
