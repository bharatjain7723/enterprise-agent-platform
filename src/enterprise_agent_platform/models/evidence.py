from pydantic import BaseModel, Field


class Evidence(BaseModel):
    title: str = Field(description="The title of the evidence")
    source: str = Field(description="The source URL or docs of this evidence")
    summary: str = Field(
        description="A summary of the snippet from the source material which supports this evidence"
    )
