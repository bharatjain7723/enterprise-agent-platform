from agents import WebSearchTool
from src.agents.base import BaseAgent
from src.prompts.researcher import RESEARCHER_INSTRUCTIONS


class ResearcherAgent(BaseAgent):
    def __init__(self) -> None:
        super().__init__(
            name="Researcher",
            description="Researches on the user input",
            instructions=RESEARCHER_INSTRUCTIONS,
            tools=[
                WebSearchTool(),
            ],
        )
