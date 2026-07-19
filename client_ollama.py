import json
import ollama
import click
from fastmcp import Client as MCPClient
import asyncio
import sys

OLLAMA_MODEL="llama3.2"
MCP_SERVER_URL="http://127.0.0.1:8080/mcp"


async def load_mcp_tools():
    """
    Connect to MCP server and get list of available tools
    """

    try:
        async with MCPClient(MCP_SERVER_URL) as mcp:
            tools_list=await mcp.list_tools()

            ollama_tools=[]
            for tool in tools_list:
                ollama_tools.append(
                    {
                        "type" : "function",
                        "function" : {
                            "name" : tool.name,
                            "description" : tool.description,
                            "parameters" : tool.inputSchema,
                        },
                    }
                )
            return ollama_tools
    except Exception as e:
        print(f"Error connecting to MCP server : {e}")
        print(f"\n Make sure the server is running")
        sys.exit(1)

async def execute_tool(tool_name: str, arguments: dict):
    """
    Call a tool on the MCP server with given arguments
    """

    try:
        async with MCPClient(MCP_SERVER_URL) as mcp:
            result = await mcp.call_tool(tool_name, arguments)
            return result
    except Exception as e:
        print(f"Error executing tool {tool_name}: {e}")
        return {"error" : str(e)}
    


async def main():
    print(f"Loading MCP tools")
    tools = await load_mcp_tools()
    print(f"Loaded {len(tools)} tools:")
    for tool in tools:
        print(f"    - {tool['function']['name']} : {tool['function']['description']}")
    print()


    while True:
        user_msg = click.prompt("\n Ask me anything. Type ':q' or 'quit' to exit:")

        if user_msg.strip().lower() in ("quit", ":q"):
            break

        # user_msg = "List all tables in Vegayan_BRAS database"
        print(f"User : {user_msg}")

        try:
            response = ollama.chat(
                model=OLLAMA_MODEL,
                messages=[
                    {
                        "role": "user",
                        "content": user_msg
                    }
                ],
                tools=tools,
                stream=False
            )
        except Exception as e:
            print(f"Error calling Ollama : {e}")
            print("\nMake sure:")
            print(f"    1. Ollama is running (ollama serve)")
            print(f"    2. Model is installed (ollama list)")
            print(f"    If not, ollama pull {OLLAMA_MODEL}")
            sys.exit(1)

        if not response.get('message', {}).get("tool_calls"):
            print("AI answered directly (no tools needed):")
            print(response["message"]["content"])
            return
        
        messages = [
            {
                "role": "user",
                "content": user_msg
            }
        ]

        for tool_call in response["message"]["tool_calls"]:
            tool_name=tool_call["function"]["name"]
            args=tool_call["function"]["arguments"]

            if isinstance(args, str):
                args=json.loads(args)

            print(f"Tool requested : {tool_name}")
            print(f"Arguments : {args}")

            tool_result = await execute_tool(tool_name, args)
            print(f"Tool result : {tool_result}\n")

            messages.append(
                {
                    "role": "tool",
                    "content": json.dumps(tool_result) if isinstance(tool_result, dict) else str(tool_result),
                }
            )
        
        # final = ollama.chat(
        #     model=OLLAMA_MODEL,
        #     messages=messages,
        # )
        
        # print(f"Final AI Response")
        # print(final["message"]["content"])
        



if __name__ == "__main__":
    asyncio.run(main())
