import asyncio
import sys

from mcp.client.session import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client


async def main() -> bool:
    server_parameters = StdioServerParameters(command="uv", args=["run", "coreason-mcp"])

    try:
        async with (
            stdio_client(server_parameters) as (read_stream, write_stream),
            ClientSession(read_stream, write_stream) as session,
        ):
            await session.initialize()
            tools_response = await session.list_tools()

            tool_names = [tool.name for tool in tools_response.tools]

            if "list_schemas" not in tool_names or "get_schema" not in tool_names:
                print(f"Error: Expected tools missing. Found tools: {tool_names}")
                return False

            print("MCP ping successful. Required tools present.")
            return True
    except Exception as e:
        print(f"Error communicating with MCP server: {e}")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    if not success:
        sys.exit(1)
