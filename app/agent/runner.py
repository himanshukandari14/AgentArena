import asyncio
import json
import os
import logging
from typing import Any

from dotenv import load_dotenv
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

load_dotenv()
logger = logging.getLogger(__name__)

server_params = StdioServerParameters(
    command="uv",
    args=["run", "python", "app/mcp/server.py"],
    env={**os.environ, "PYTHONPATH": "."},
)


async def run_agent_for_task(
    task_description: str,
    max_iterations: int = 20,
) -> dict[str, Any]:
    """
    Executes an AI agent for a specific task using the FastMCP server tools.
    Supports standard OpenAI API client or robust fallback execution for evaluation.
    Returns dictionary with output_text, tool_calls log, and optional error.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    tool_calls_executed = []

    if not api_key:
        logger.warning("OPENAI_API_KEY not set. Running simulated/deterministic evaluation mode.")
        return {
            "output_text": "Agent executed in benchmark evaluation mode.",
            "tool_calls": tool_calls_executed,
            "error": "No API key configured.",
        }

    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)

        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                tools_result = await session.list_tools()

                openai_tools = [
                    {
                        "type": "function",
                        "name": tool.name,
                        "description": tool.description or "",
                        "parameters": tool.inputSchema,
                    }
                    for tool in tools_result.tools
                ]

                messages = [
                    {
                        "role": "system",
                        "content": (
                            "You are an AI agent operating inside the AgentForge environment. "
                            "Use the available tools to complete the requested task completely. "
                            "Do not invent IDs or facts."
                        ),
                    },
                    {"role": "user", "content": task_description},
                ]

                final_output = ""
                for iteration in range(max_iterations):
                    response = client.responses.create(
                        model="gpt-4o-mini",
                        input=messages,
                        tools=openai_tools,
                    )

                    tool_calls = [item for item in response.output if item.type == "function_call"]

                    if not tool_calls:
                        final_output = getattr(response, "output_text", "Completed.")
                        break

                    for tool_call in tool_calls:
                        args = json.loads(tool_call.arguments)
                        try:
                            result = await session.call_tool(tool_call.name, args)
                            success = True
                            content = result.content
                        except Exception as te:
                            success = False
                            content = str(te)

                        tool_calls_executed.append({
                            "name": tool_call.name,
                            "arguments": args,
                            "result": content,
                            "success": success,
                        })

                        messages.append({
                            "type": "function_call",
                            "call_id": tool_call.call_id,
                            "name": tool_call.name,
                            "arguments": tool_call.arguments,
                        })

                        messages.append({
                            "type": "function_call_output",
                            "call_id": tool_call.call_id,
                            "output": json.dumps(content, default=str),
                        })

                return {
                    "output_text": final_output,
                    "tool_calls": tool_calls_executed,
                    "error": None,
                }

    except Exception as e:
        logger.error(f"Agent execution error: {e}", exc_info=True)
        return {
            "output_text": "",
            "tool_calls": tool_calls_executed,
            "error": str(e),
        }


if __name__ == "__main__":
    test_task = "Find all open or pending tickets belonging to customers with overdue invoices and assign to Billing."
    res = asyncio.run(run_agent_for_task(test_task))
    print("Agent Result:", res)