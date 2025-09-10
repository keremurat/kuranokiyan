from mcp.server.fastmcp import FastMCP
from app import dummyTool

# Initialize MCP server
mcp = FastMCP("your-mcp-name")

@mcp.tool()
async def dummy_tool(param: str) -> str:
    """
    Definition of a tool here.
    """
    # Do some awsome processing here
    awsome_response = dummyTool(param)
    if not awsome_response:
        return "No awsome response found."

    return 

# Your another awsome tools can be added here
# @mcp.tool()
# async def another_awsome_tool(param: str) -> str:
#     """
#     Get better at AI.
#     """
#     # Do some awsome processing here
#     return "You are getting better at AI!"


if __name__ == "__main__":
    mcp.run(transport="stdio")