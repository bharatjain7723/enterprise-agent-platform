import asyncio
from datetime import UTC, datetime
from pathlib import Path

from agents import Agent, Runner
from dotenv import load_dotenv
from openai import AsyncOpenAI

from enterprise_agent_platform.knowledge.embedding_repository import (
    EmbeddingRepository,
)
from enterprise_agent_platform.knowledge.file_index_store import FileIndexStore
from enterprise_agent_platform.models.knowledge_document import KnowledgeDocument
from enterprise_agent_platform.services.documentation import DocumentationService
from enterprise_agent_platform.services.embedding import OpenAIEmbeddingService
from enterprise_agent_platform.tools.calculator import add
from enterprise_agent_platform.tools.documentation_search import (
    create_documentation_search_tool,
)

load_dotenv()


async def main() -> None:
    client = AsyncOpenAI()

    embedding_service = OpenAIEmbeddingService(
        client=client,
    )

    repository = EmbeddingRepository(
        embedding_service=embedding_service,
        index_store=FileIndexStore(Path("data/semantic_index.json")),
    )

    documents = [
        KnowledgeDocument(
            id="generators",
            title="Python Generators",
            content=(
                "Python generators produce values lazily using the "
                "yield keyword. They are useful for processing "
                "large sequences without loading everything into memory."
            ),
            source="",
            updated_at=datetime.now(UTC),
        ),
        KnowledgeDocument(
            id="asyncio",
            title="AsyncIO",
            content=(
                "AsyncIO provides asynchronous programming capabilities "
                "in Python and is useful for I/O-bound workloads."
            ),
            source="",
            updated_at=datetime.now(UTC),
        ),
    ]

    await repository.index_documents(documents)

    documentation_service = DocumentationService(
        searcher=repository,
    )

    documentation_tool = create_documentation_search_tool(
        documentation_service,
    )

    agent = Agent(
        name="Math Assistant",
        instructions="""
        You are a helpful math assistant.

        Use tools whenever appropriate.
        """,
        tools=[add, documentation_tool],
    )

    result = await Runner.run(
        agent,
        "Research Python generators.",
    )

    print(result.final_output)


if __name__ == "__main__":
    asyncio.run(main())
