"""MCP server exposing enterprise knowledge-search tools."""

from typing import TypedDict

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("enterprise-knowledge")


KNOWLEDGE_BASE: dict[str, str] = {
    "deployment": (
        "Deployments use Terraform to provision infrastructure. "
        "Changes must pass validation before reaching production."
    ),
    "security": (
        "Production services must use TLS. Secrets must be stored "
        "in a managed secrets vault and must not be committed to source control."
    ),
    "database": (
        "Database migrations must be tested before production rollout. "
        "Applications should use connection pooling and secure credentials."
    ),
}


class KnowledgeEntry(TypedDict):
    topic: str
    content: str


class ScoredKnowledgeEntry(TypedDict):
    topic: str
    content: str
    score: int


@mcp.tool()
def search_knowledge(query: str) -> dict[str, object]:
    """Search enterprise knowledge using matching words and topics.

    Args:
        query: A word or phrase to search for.
    """
    normalized_query = query.strip().lower()

    if not normalized_query:
        return {
            "query": query,
            "results": [],
            "count": 0,
            "message": "Query must not be empty.",
        }

    query_terms = set(normalized_query.split())
    scored_entries: list[ScoredKnowledgeEntry] = []

    for topic, content in KNOWLEDGE_BASE.items():
        normalized_topic = topic.lower()
        normalized_content = content.lower()

        matching_terms = {
            term for term in query_terms if term in normalized_topic or term in normalized_content
        }

        if matching_terms:
            scored_entries.append(
                {
                    "topic": topic,
                    "content": content,
                    "score": len(matching_terms),
                }
            )

    scored_entries.sort(
        key=lambda entry: entry["score"],
        reverse=True,
    )

    results: list[KnowledgeEntry] = [
        {"topic": entry["topic"], "content": entry["content"]} for entry in scored_entries
    ]

    return {
        "query": query,
        "results": results,
        "count": len(results),
    }


if __name__ == "__main__":
    mcp.run(transport="stdio")
