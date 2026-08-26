import asyncio
from pathlib import Path

from enterprise_agent_platform.knowledge.markdown_repository import MarkdownKnowledgeRepository

SEARCH_CASES = [
    (
        "asyncio",
        "asyncio",
    ),
    (
        "asynchronous programming",
        "asyncio",
    ),
    (
        "async programming",
        "asyncio",
    ),
    (
        "parallel execution",
        "asyncio",
    ),
    (
        "retry policy",
        "retry",
    ),
    (
        "exception recovery",
        "retry",
    ),
]

repository = MarkdownKnowledgeRepository(Path("docs/knowledge"))


async def main() -> None:
    for query, _expected_document in SEARCH_CASES:
        results = await repository.search(query)
        print(results)


if __name__ == "__main__":
    asyncio.run(main())
