from pydantic import BaseModel, Field


class CodeFile(BaseModel):
    path: str = Field(description="The path to the file")
    content: str = Field(
        description="The code content of the file, including any imports and other dependenciesWWW"
    )
