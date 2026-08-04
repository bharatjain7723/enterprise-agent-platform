import asyncio

from dotenv import load_dotenv

from enterprise_agent_platform.orchestration.worker import WorkerOrchestrator

load_dotenv()


async def main():
    worker = WorkerOrchestrator()

    result = await worker.run(
        """
        Build an AI Interview Copilot for software engineers.
        """
    )

    # print(result)
    print(result.model_dump_json(indent=2))


if __name__ == "__main__":
    asyncio.run(main())
