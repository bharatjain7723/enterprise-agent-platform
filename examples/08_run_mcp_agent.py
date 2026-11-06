"""Run an agent that discovers and uses tools from an MCP server."""

import asyncio
import sys

from agents import Agent, Runner
from agents.mcp import MCPServerStdio, MCPServerStdioParams
from dotenv import load_dotenv

load_dotenv()


async def main() -> None:
    server_params: MCPServerStdioParams = {
        "command": sys.executable,
        "args": [
            "-m",
            "enterprise_agent_platform.mcp_servers.knowledge_server",
        ],
    }

    async with MCPServerStdio(
        params=server_params,
        name="Enterprise Knowledge Server",
    ) as server:
        agent = Agent(
            name="Enterprise Knowledge Assistant",
            instructions=(
                "You answer questions using the enterprise knowledge search tool. "
                "When asked about enterprise policies or practices, call the "
                "search_knowledge tool to retrieve relevant information. "
                "Clearly state when the available knowledge does not answer "
                "the question. Do not invent enterprise policies."
            ),
            mcp_servers=[server],
        )

        result = await Runner.run(
            agent,
            "What security practices are required for production services?",
        )

        print(result.final_output)


if __name__ == "__main__":
    asyncio.run(main())
