from typing import TypedDict

from enterprise_agent_platform.mcp_servers.knowledge_server import (
    search_knowledge,
)


class KnowledgeEntry(TypedDict):
    topic: str
    content: str


def test_search_knowledge_finds_matching_topic() -> None:
    result = search_knowledge("security")

    assert result["count"] == 1
    results = result["results"]
    assert isinstance(results, list)
    assert results[0]["topic"] == "security"


def test_search_knowledge_finds_matching_content() -> None:
    result = search_knowledge("Terraform")

    assert result["count"] == 1
    results = result["results"]
    assert isinstance(results, list)
    assert results[0]["topic"] == "deployment"


def test_search_knowledge_rejects_blank_query() -> None:
    result = search_knowledge("   ")

    assert result["count"] == 0
    assert result["message"] == "Query must not be empty."


def test_search_knowledge_returns_no_matches() -> None:
    result = search_knowledge("nonexistent-topic")

    assert result["count"] == 0


def test_search_knowledge_matches_multiple_query_terms() -> None:
    result = search_knowledge("production services security practices required")

    assert result["count"] >= 1

    raw_results = result["results"]
    assert isinstance(raw_results, list)

    expected_security_entry = {
        "topic": "security",
        "content": (
            "Production services must use TLS. Secrets must be stored "
            "in a managed secrets vault and must not be committed to source control."
        ),
    }

    assert expected_security_entry in raw_results
