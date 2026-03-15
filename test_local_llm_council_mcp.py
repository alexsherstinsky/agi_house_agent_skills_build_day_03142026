import asyncio
import sys

from mcp import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client

SERVER_PARAMS = StdioServerParameters(
    command=".venv/bin/python3",
    args=["-m", "llm_council_mcp.server"],
)


async def run_tests():
    async with stdio_client(SERVER_PARAMS) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # Test 1: tool is listed
            tools = await session.list_tools()
            tool_names = [t.name for t in tools.tools]
            assert "llm_council_evaluate" in tool_names, f"Expected tool not found: {tool_names}"
            print("✓ llm_council_evaluate tool is listed")

            # Test 2: tool returns a non-empty response
            result = await session.call_tool(
                "llm_council_evaluate",
                {"artifact": "def add(a, b):\n    return a + b"},
            )
            assert result.content, "Tool returned empty content"
            text = result.content[0].text
            assert len(text) > 100, f"Response too short: {text!r}"
            print("✓ llm_council_evaluate returned a non-empty evaluation prompt")
            print(f"\nFirst 300 chars of response:\n{text[:300]}")


if __name__ == "__main__":
    try:
        asyncio.run(run_tests())
        print("\nAll tests passed.")
    except Exception as e:
        print(f"\nTest failed: {e}", file=sys.stderr)
        sys.exit(1)
