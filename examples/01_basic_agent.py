import asyncio

from enterprise_agent_platform.agents.planner import PlannerAgent


async def main() -> None:
    planner = PlannerAgent()

    result = await planner.run("Build an AI Interview Copilot for software engineers.")

    print(result.model_dump_json(indent=2))


if __name__ == "__main__":
    asyncio.run(main())
