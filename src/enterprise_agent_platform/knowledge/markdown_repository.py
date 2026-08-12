from pathlib import Path

from enterprise_agent_platform.models.knowledge_document import KnowledgeDocument
from enterprise_agent_platform.models.knowledge_search_result import KnowledgeSearchResult


class MarkdownKnowledgeRepository:
    """Loads knowledge from Markdown documents."""

    def __init__(
        self,
        docs_directory: Path,
    ) -> None:
        self.docs_directory = docs_directory

    def search(
        self,
        query: str,
    ) -> list[KnowledgeSearchResult]:
        terms = query.lower().split()

        search_results: list[KnowledgeSearchResult] = []

        for document in self._load_documents():
            score = self._calculate_score(
                document,
                terms,
            )

            if score > 0:
                search_results.append(
                    KnowledgeSearchResult(
                        document=document,
                        score=score,
                        snippet=self._generate_snippet(
                            document,
                            terms,
                        ),
                    )
                )

        search_results.sort(
            key=lambda result: result.score,
            reverse=True,
        )

        return search_results

    def _calculate_score(
        self,
        document: KnowledgeDocument,
        terms: list[str],
    ) -> int:
        content = document.content.lower()

        score = 0

        for term in terms:
            score += content.count(term)

        return score

    def _calculate_line_score(
        self,
        line: str,
        terms: list[str],
    ) -> int:
        keyword_matches = 0

        content = line.lower()

        for term in terms:
            keyword_matches += content.count(term)

        if keyword_matches == 0:
            return 0

        return keyword_matches * 100 + min(len(line), 80)

    def _generate_snippet(
        self,
        document: KnowledgeDocument,
        terms: list[str],
    ) -> str:
        best_score = -1
        best_line = ""

        for line in document.content.splitlines():
            score = self._calculate_line_score(
                line,
                terms,
            )

            if score > best_score:
                best_score = score
                best_line = line.strip()

        return best_line

    def _load_documents(
        self,
    ) -> list[KnowledgeDocument]:
        documents: list[KnowledgeDocument] = []

        for path in self.docs_directory.glob("*.md"):
            # print(f"path: {path}")

            documents.append(
                KnowledgeDocument(
                    id=path.stem,
                    title=path.stem.replace("_", " ").title(),
                    source=str(path),
                    content=path.read_text(encoding="utf-8"),
                )
            )

        return documents


# example testing
# repository = MarkdownKnowledgeRepository(
#     Path("C:/Users/Ajay Jain/Desktop/AI Core project/enterprise-agent-platform/docs/knowledge")
# )

# results = repository.search("asyncio")

# print(results)

# print(results[0].score)
