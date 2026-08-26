import asyncio
from pathlib import Path

from enterprise_agent_platform.agents.coder import CoderAgent
from enterprise_agent_platform.agents.researcher import ResearcherAgent
from enterprise_agent_platform.knowledge.markdown_repository import (
    MarkdownKnowledgeRepository,
)
from enterprise_agent_platform.models.worker_type import WorkerType
from enterprise_agent_platform.orchestration.registry import AgentRegistry
from enterprise_agent_platform.services.documentation import DocumentationService

repository = MarkdownKnowledgeRepository(Path("docs/knowledge"))

documentation_service = DocumentationService(
    searcher=repository,
)

registry = AgentRegistry()

registry.register(
    WorkerType.RESEARCHER,
    ResearcherAgent(
        documentation_service=documentation_service,
    ),
)

registry.register(
    WorkerType.CODER,
    CoderAgent(),
)

assert registry.contains(WorkerType.RESEARCHER)

researcher = registry.get(WorkerType.RESEARCHER)
coder = registry.get(WorkerType.CODER)


async def run():
    result = await researcher.run("Explain Python decorators.")
    return result


if __name__ == "__main__":
    result = asyncio.run(run())
    print(result)
