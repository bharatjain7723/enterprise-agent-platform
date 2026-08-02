from enterprise_agent_platform.agents.base import BaseAgent
from enterprise_agent_platform.models.plan import Plan
from enterprise_agent_platform.prompts.planner import PLANNER_INSTRUCTIONS


class PlannerAgent(BaseAgent[Plan]):
    def __init__(self) -> None:
        super().__init__(
            name="Planner",
            description="Breaks complex objectives into structured execution plans.",
            instructions=PLANNER_INSTRUCTIONS,
            output_type=Plan,
        )
