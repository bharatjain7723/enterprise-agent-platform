from agents import function_tool

from enterprise_agent_platform.models.knowledge_search_result import (
    KnowledgeSearchResult,
)
from enterprise_agent_platform.services.protocols import DocumentationSearcher


def create_documentation_search_tool(
    service: DocumentationSearcher,
):
    @function_tool
    async def search_documentation(
        query: str,
    ) -> str:
        """
        Search the project documentation.

        Use this tool whenever the user asks about
        Python, OpenAI Agents SDK,
        Enterprise Agent Platform,
        architecture,
        implementation,
        or documentation.
        """
        results: list[KnowledgeSearchResult] = await service.search(query)

        if not results:
            return "No relevant documentation was found."

        formatted_results: list[str] = []

        for index, result in enumerate(results, start=1):
            formatted_results.append(
                f"[{index}] {result.document.title}\n"
                f"Source: {result.document.source}\n"
                f"Relevance: {result.score:.3f}\n"
                f"{result.document.content}"
            )

        return "\n\n".join(formatted_results)

    return search_documentation
