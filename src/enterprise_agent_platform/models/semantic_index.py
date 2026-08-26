from pydantic import BaseModel, Field

from enterprise_agent_platform.models.embedded_document import EmbeddedDocument
from enterprise_agent_platform.models.embedding_metadata import EmbeddingMetadata


class SemanticIndex(BaseModel):
    metadata: EmbeddingMetadata = Field(
        description="Metadata describing the embeddings in the index"
    )

    documents: list[EmbeddedDocument] = Field(
        default_factory=lambda: [], description="Documents and their embeddings"
    )
