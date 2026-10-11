from agents import Tool, WebSearchTool

from enterprise_agent_platform.agents.base import BaseAgent
from enterprise_agent_platform.memory.service import MemoryService
from enterprise_agent_platform.models.research_result import ResearchResult
from enterprise_agent_platform.prompts.researcher import RESEARCHER_INSTRUCTIONS
from enterprise_agent_platform.services.documentation import DocumentationService
from enterprise_agent_platform.tools.documentation_search import (
    create_documentation_search_tool,
)
from enterprise_agent_platform.tools.memory import create_memory_tools


class ResearcherAgent(BaseAgent[ResearchResult]):
    def __init__(
        self,
        documentation_service: DocumentationService,
        memory_service: MemoryService | None = None,
    ) -> None:
        documentation_tool = create_documentation_search_tool(documentation_service)

        tools: list[Tool] = [
            WebSearchTool(),
            documentation_tool,
        ]

        if memory_service is not None:
            memory_tools = create_memory_tools(memory_service)
            tools.extend(memory_tools)

        super().__init__(
            name="Researcher",
            description="Researches on the assigned task input",
            instructions=RESEARCHER_INSTRUCTIONS,
            output_type=ResearchResult,
            tools=tools,
        )
