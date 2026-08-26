from datetime import datetime

from pydantic import BaseModel, Field


class KnowledgeDocument(BaseModel):
    """A document stored in the knowledge base."""

    id: str = Field(description="Unique document identifier.")

    title: str = Field(description="Human-readable document title.")

    content: str = Field(description="Full document content.")

    source: str = Field(description="Original source of the document.")

    updated_at: datetime = Field(description="time of updating the document")
