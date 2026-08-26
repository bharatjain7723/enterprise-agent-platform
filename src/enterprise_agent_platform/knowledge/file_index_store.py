import json
from pathlib import Path

from enterprise_agent_platform.models.semantic_index import SemanticIndex


class FileIndexStore:
    """Persists a semantic index to a JSON file."""

    def __init__(
        self,
        path: Path,
    ) -> None:
        self.path = path

    async def save(
        self,
        index: SemanticIndex,
    ) -> None:
        self.path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        data = index.model_dump(mode="json")

        with self.path.open("w", encoding="utf-8") as file:
            json.dump(
                data,
                file,
                indent=2,
            )

    async def load(
        self,
    ) -> SemanticIndex | None:
        if not self.path.exists():
            return None

        data = json.loads(
            self.path.read_text(
                encoding="utf-8",
            )
        )

        return SemanticIndex.model_validate(data)
