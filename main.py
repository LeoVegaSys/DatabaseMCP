from fastmcp import FastMCP
from ratelimiter import check_rate_limit
from db import execute_procedure_call, run_query
from discovery_tools import register_discovery_tools
from tool_generator import register_database_tools


mcp = FastMCP("Database_MCP_Server", auth=None)


# register system discovery tools
register_discovery_tools(mcp)


# register dynamic database tools
# register_database_tools(mcp)

@mcp.tool()
def call_procedure(procedure_name: str, parameters: list = None):
    """
    Execute a stored procedure by providing necessary arguments    """

    check_rate_limit()

    return execute_procedure_call(procedure_name, parameters or [])

mcp.tool()(run_query)

if __name__ == "__main__":
    #mcp.run(transport="streamable-http", host="127.0.0.1", port=8080)
    mcp.run(transport="streamable-http", host="127.0.0.1", port=8083, json_response=True, stateless_http=True)
