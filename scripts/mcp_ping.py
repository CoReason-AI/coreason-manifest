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

            # The server is now passive. We verify it has NO tools, but HAS resource templates.
            tools_response = await session.list_tools()
            if len(tools_response.tools) > 0:
                print(f"Error: Server must be strictly passive. Found active tools: {tools_response.tools}")
                return False

            templates_response = await session.list_resource_templates()
            templates = [template.uriTemplate for template in templates_response.resourceTemplates]

            required_templates = [
                "schema://epistemic/{name}",
                "schema://state/memoized/{hash}",
                "schema://capabilities/{profile}",
            ]

            for req in required_templates:
                if req not in templates:
                    print(f"Error: Missing required resource template {req}. Found: {templates}")
                    return False

            print("MCP ping successful. Server is strictly passive and projects proper ontological resources.")
            return True
    except Exception as e:
        print(f"Error communicating with MCP server: {e}")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    if not success:
        sys.exit(1)
