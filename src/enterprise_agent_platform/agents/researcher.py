from agents import WebSearchTool

from enterprise_agent_platform.agents.base import BaseAgent
from enterprise_agent_platform.models.research_result import ResearchResult
from enterprise_agent_platform.prompts.researcher import RESEARCHER_INSTRUCTIONS


class ResearcherAgent(BaseAgent[ResearchResult]):
    def __init__(self) -> None:
        super().__init__(
            name="Researcher",
            description="Researches on the assigned task input",
            instructions=RESEARCHER_INSTRUCTIONS,
            output_type=ResearchResult,
            tools=[
                WebSearchTool(),
            ],
        )
