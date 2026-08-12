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

for query, _expected_document in SEARCH_CASES:
    results = repository.search(query)

    print(results)
