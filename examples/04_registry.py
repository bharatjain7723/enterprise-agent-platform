from enterprise_agent_platform.agents.coder import CoderAgent
from enterprise_agent_platform.agents.researcher import ResearcherAgent
from enterprise_agent_platform.models.worker_type import WorkerType
from enterprise_agent_platform.orchestration.registry import AgentRegistry

registry = AgentRegistry()

registry.register(
    WorkerType.RESEARCHER,
    ResearcherAgent(),
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


print(run())
