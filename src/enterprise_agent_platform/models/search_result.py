from pydantic import BaseModel, Field


class SearchResult(BaseModel):
    title: str = Field(description="Document title")

    url: str = Field(description="Document URL")

    snippet: str = Field(description="Relevant snippet")
