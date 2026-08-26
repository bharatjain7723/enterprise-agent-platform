from agents import WebSearchTool

from enterprise_agent_platform.agents.base import BaseAgent
from enterprise_agent_platform.models.research_result import ResearchResult
from enterprise_agent_platform.prompts.researcher import RESEARCHER_INSTRUCTIONS
from enterprise_agent_platform.services.documentation import DocumentationService
from enterprise_agent_platform.tools.documentation_search import (
    create_documentation_search_tool,
)


class ResearcherAgent(BaseAgent[ResearchResult]):
    def __init__(
        self,
        documentation_service: DocumentationService,
    ) -> None:
        documentation_tool = create_documentation_search_tool(
            documentation_service,
        )

        super().__init__(
            name="Researcher",
            description="Researches on the assigned task input",
            instructions=RESEARCHER_INSTRUCTIONS,
            output_type=ResearchResult,
            tools=[
                WebSearchTool(),
                documentation_tool,
            ],
        )
