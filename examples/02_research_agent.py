import asyncio

from dotenv import load_dotenv

from enterprise_agent_platform.agents.researcher import ResearcherAgent

load_dotenv()


async def main():
    researcher = ResearcherAgent()

    result = await researcher.run(
        """
        What were the biggest news in the AI industry yeaterday?
        """
    )

    print(result)
    print(result.model_dump_json(indent=2))


if __name__ == "__main__":
    asyncio.run(main())
