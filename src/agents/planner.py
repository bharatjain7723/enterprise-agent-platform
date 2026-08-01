from agents import Agent, Runner
from src.agents.base import BaseAgent
from src.prompts.planner import PLANNER_INSTRUCTIONS

planner = Agent(
    name="Planner",
    instructions=PLANNER_INSTRUCTIONS,
)


class PlannerAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="planner",
            description="Creates execution plans.",
        )

    async def run(self, user_input: str) -> str:
        result = await Runner.run(
            planner,
            input=user_input,
        )

        return result.final_output
