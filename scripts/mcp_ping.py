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

            if len(tool_names) > 0:
                print(f"Error: Expected ZERO tools (passive boundary). Found tools: {tool_names}")
                return False

            # Let's just ensure we can list resources or templates if supported.
            # The endpoints defined are resource templates, not static resources.
            templates_response = await session.list_resource_templates()
            template_uris = [tpl.uriTemplate for tpl in templates_response.resourceTemplates]

            if not any("epistemic" in tpl for tpl in template_uris):
                print(f"Error: Expected epistemic resource template. Found templates: {template_uris}")
                return False

            print("MCP ping successful. Server is properly passive with correct resource templates.")
            return True
    except Exception as e:
        print(f"Error communicating with MCP server: {e}")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    if not success:
        sys.exit(1)
