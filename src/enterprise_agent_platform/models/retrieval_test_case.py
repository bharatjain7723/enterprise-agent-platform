from pydantic import BaseModel, Field


class RetrievalTestCase(BaseModel):
    query: str = Field()
    expected_document_id: str = Field()
