import asyncio
import os
import pathlib
from typing import AsyncGenerator

import anthropic
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

SKILLS_DIR = pathlib.Path(__file__).parent / "skills"
MCP_SERVERS = {
    "knowledge-base": "http://localhost:8001/mcp",
    "crm": "http://localhost:8002/mcp",
    "actions": "http://localhost:8003/mcp",
}


def load_skills() -> str:
    """Load all skill markdown files into a single system prompt."""
    parts = []
    for skill_file in sorted(SKILLS_DIR.glob("*.md")):
        parts.append(
            f"## {skill_file.stem.replace('_', ' ').title()}\n\n{skill_file.read_text()}"
        )
    return "\n\n---\n\n".join(parts)


async def get_all_tools() -> tuple[list[dict], dict]:
    """Connect to all MCP servers and collect their tools.

    Returns:
        (tools_for_claude, tool_to_server_map)
    """
    all_tools: list[dict] = []
    tool_server_map: dict[str, str] = {}

    for server_name, server_url in MCP_SERVERS.items():
        try:
            async with streamablehttp_client(server_url) as (read, write, _):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    result = await session.list_tools()
                    for tool in result.tools:
                        tool_dict = {
                            "name": tool.name,
                            "description": tool.description,
                            "input_schema": tool.inputSchema,
                        }
                        all_tools.append(tool_dict)
                        tool_server_map[tool.name] = server_url
        except Exception as e:
            print(f"Warning: Could not connect to {server_name} at {server_url}: {e}")

    return all_tools, tool_server_map


async def call_tool(tool_name: str, tool_input: dict, server_url: str) -> str:
    """Call a specific tool on its MCP server and return the result as a string."""
    async with streamablehttp_client(server_url) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool(tool_name, tool_input)
            if result.content:
                parts = []
                for item in result.content:
                    if hasattr(item, "text"):
                        parts.append(item.text)
                return "\n".join(parts) if parts else str(result.content)
            return "Tool returned no content"


async def run_agent(messages: list[dict]) -> AsyncGenerator[dict, None]:
    """
    Run the agentic loop over the provided conversation messages.

    Yields events:
        {"type": "tool_call",   "name": str, "input": dict}
        {"type": "tool_result", "name": str, "result": str}
        {"type": "token",       "text": str}
        {"type": "done"}
        {"type": "error",       "message": str}
    """
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    system_prompt = load_skills()
    tools, tool_server_map = await get_all_tools()

    conversation = list(messages)

    while True:
        response = client.messages.create(
            model="claude-opus-4-5",
            max_tokens=4096,
            system=system_prompt,
            tools=tools if tools else [],
            messages=conversation,
        )

        if response.stop_reason == "tool_use":
            # Append the assistant's response (may contain text + tool_use blocks)
            assistant_message = {"role": "assistant", "content": response.content}
            conversation.append(assistant_message)

            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    tool_name = block.name
                    tool_input = block.input
                    tool_use_id = block.id

                    yield {"type": "tool_call", "name": tool_name, "input": tool_input}

                    server_url = tool_server_map.get(tool_name)
                    if server_url:
                        try:
                            result = await call_tool(tool_name, tool_input, server_url)
                        except Exception as e:
                            result = f"Error calling tool: {e}"
                    else:
                        result = f"Unknown tool: {tool_name}"

                    yield {"type": "tool_result", "name": tool_name, "result": result}
                    tool_results.append(
                        {
                            "type": "tool_result",
                            "tool_use_id": tool_use_id,
                            "content": result,
                        }
                    )

            conversation.append({"role": "user", "content": tool_results})
            # Continue the agentic loop

        elif response.stop_reason == "end_turn":
            # Stream the final text token by token (word-level simulation)
            for block in response.content:
                if hasattr(block, "text"):
                    words = block.text.split(" ")
                    for word in words:
                        yield {"type": "token", "text": word + " "}
                        await asyncio.sleep(0.01)
            yield {"type": "done"}
            break

        else:
            yield {
                "type": "error",
                "message": f"Unexpected stop reason: {response.stop_reason}",
            }
            break
