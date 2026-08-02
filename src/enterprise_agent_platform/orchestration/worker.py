from enterprise_agent_platform.agents.planner import PlannerAgent
from enterprise_agent_platform.models.plan import Plan


class WorkerOrchestrator:
    """Coordinates all platform agents."""

    def __init__(self):
        self.planner = PlannerAgent()

    async def run(self, task: str) -> Plan:
        return await self.planner.run(task)
