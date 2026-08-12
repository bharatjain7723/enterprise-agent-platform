from pydantic import BaseModel, Field

from enterprise_agent_platform.models.knowledge_document import (
    KnowledgeDocument,
)


class KnowledgeSearchResult(BaseModel):
    """Represents a document returned from a search."""

    document: KnowledgeDocument = Field(description="The matching knowledge document.")

    score: int = Field(ge=0, description="Relevance score.")

    snippet: str = Field(description="Snippet of the document content which matches the query")
