import json
import sys

import pytest
from mcp import ClientSession, StdioServerParameters, types
from mcp.client.stdio import stdio_client


@pytest.mark.asyncio
async def test_mcp_client_discovers_and_calls_knowledge_tool() -> None:
    server_params = StdioServerParameters(
        command=sys.executable,
        args=[
            "-m",
            "enterprise_agent_platform.mcp_servers.knowledge_server",
        ],
    )

    async with stdio_client(server_params) as (read_stream, write_stream):  # noqa: SIM117
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()

            tools_result = await session.list_tools()
            tool_names = [tool.name for tool in tools_result.tools]

            assert "search_knowledge" in tool_names

            call_result = await session.call_tool(
                "search_knowledge",
                {"query": "security"},
            )

            assert not call_result.isError

            text_blocks = [
                item.text for item in call_result.content if isinstance(item, types.TextContent)
            ]
            assert text_blocks

            result = json.loads(text_blocks[0])
            assert result["count"] == 1
            assert result["results"][0]["topic"] == "security"
