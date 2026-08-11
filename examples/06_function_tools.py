import asyncio

from agents import Agent, Runner
from dotenv import load_dotenv

from enterprise_agent_platform.services.documentation import DocumentationService
from enterprise_agent_platform.tools.calculator import add
from enterprise_agent_platform.tools.documentation_search import create_documentation_search_tool

load_dotenv()

documentation_service = DocumentationService()

documentation_tool = create_documentation_search_tool(documentation_service)


async def main() -> None:
    agent = Agent(
        name="Math Assistant",
        instructions="""
        You are a helpful math assistant.

        Use tools whenever appropriate.
        """,
        tools=[add, documentation_tool],
    )

    result = await Runner.run(
        agent,
        "Research Python generators.",
    )

    print(result.final_output)


if __name__ == "__main__":
    asyncio.run(main())
