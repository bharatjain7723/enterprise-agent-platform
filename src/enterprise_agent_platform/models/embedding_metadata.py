from pydantic import BaseModel, Field


class EmbeddingMetadata(BaseModel):
    provider: str = Field(description="Embedding provider")

    model: str = Field(description="Embedding model")

    dimensions: int = Field(description="Number of dimensions in each embedding")

    index_version: int = Field(description="Version of the persisted index format")
