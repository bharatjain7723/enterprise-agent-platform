import asyncio

from dotenv import load_dotenv

from src.agents.researcher import ResearcherAgent

load_dotenv()


async def main():
    researcher = ResearcherAgent()

    result = await researcher.run(
        """
        What were the biggest news in the stock market yesterday?
        """
    )

    print(result)


if __name__ == "__main__":
    asyncio.run(main())
