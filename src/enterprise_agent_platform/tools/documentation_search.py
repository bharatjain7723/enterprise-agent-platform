from agents import function_tool

from enterprise_agent_platform.services.protocols import DocumentationSearcher


def create_documentation_search_tool(
    service: DocumentationSearcher,
):
    @function_tool
    def search_documentation(
        query: str,
    ):
        """
        Search the project documentation.

        Use this tool whenever the user asks about
        Python, OpenAI Agents SDK,
        Enterprise Agent Platform,
        architecture,
        implementation,
        or documentation.
        """

        return service.search(query)

    return search_documentation
