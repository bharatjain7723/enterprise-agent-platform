from src.agents.base import BaseAgent
from src.prompts.planner import PLANNER_INSTRUCTIONS


class PlannerAgent(BaseAgent):
    def __init__(self) -> None:
        super().__init__(
            name="Planner",
            description="Breaks complex objectives into structured execution plans.",
            instructions=PLANNER_INSTRUCTIONS,
        )
