import asyncio

from dotenv import load_dotenv

from enterprise_agent_platform.agents.coder import CoderAgent
from enterprise_agent_platform.agents.planner import PlannerAgent
from enterprise_agent_platform.agents.researcher import ResearcherAgent
from enterprise_agent_platform.models.worker_type import WorkerType
from enterprise_agent_platform.orchestration.registry import AgentRegistry
from enterprise_agent_platform.orchestration.worker import WorkerOrchestrator

load_dotenv()


async def main() -> None:
    # 1. Create our agents
    planner = PlannerAgent()
    researcher = ResearcherAgent()
    coder = CoderAgent()

    # 2. Register worker agents
    registry = AgentRegistry()

    registry.register(
        WorkerType.RESEARCHER,
        researcher,
    )

    registry.register(
        WorkerType.CODER,
        coder,
    )

    # 3. Create the orchestrator
    worker = WorkerOrchestrator(
        registry=registry,
    )

    # 4. User input
    user_input = """
    Research Python's functools.lru_cache and create a small Python
    example demonstrating when and how to use it.
    """

    # 5. Planner converts user input → Plan
    plan = await planner.run(user_input)

    print("\n========== PLAN ==========\n")
    print(plan.model_dump_json(indent=2))

    # 6. Worker executes the Plan
    results = await worker.execute(plan)

    # 7. Print results
    print("\n========== RESULTS ==========\n")

    for task_id, task_result in results.items():
        print(f"\n--- {task_id} ---")
        print(task_result.output)


if __name__ == "__main__":
    asyncio.run(main())
