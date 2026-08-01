from src.agents.planner import PlannerAgent


class WorkerOrchestrator:
    """Coordinates all platform agents."""

    def __init__(self):
        self.planner = PlannerAgent()

    async def run(self, task: str) -> str:
        return await self.planner.run(task)
