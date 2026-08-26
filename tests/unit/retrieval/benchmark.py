import asyncio
from pathlib import Path

from enterprise_agent_platform.knowledge.markdown_repository import MarkdownKnowledgeRepository
from enterprise_agent_platform.models.retrieval_test_case import RetrievalTestCase

SEARCH_CASES = [
    RetrievalTestCase(
        query="asyncio",
        expected_document_id="asyncio",
    ),
    RetrievalTestCase(
        query="asynchronous programming",
        expected_document_id="asyncio",
    ),
    RetrievalTestCase(
        query="retry policy",
        expected_document_id="retry_policy",
    ),
    RetrievalTestCase(
        query="structured outputs",
        expected_document_id="pydantic",
    ),
]


async def main() -> None:
    repository = MarkdownKnowledgeRepository(Path("docs/knowledge"))

    correct = 0

    for case in SEARCH_CASES:
        results = await repository.search(case.query)

        if not results:
            continue

        if results[0].document.id == case.expected_document_id:
            correct += 1

    accuracy = correct / len(SEARCH_CASES)

    print(f"Queries Tested: {len(SEARCH_CASES)}")
    print(f"Correct: {correct}")
    print(f"Accuracy: {accuracy * 100}%")


if __name__ == "__main__":
    asyncio.run(main())
