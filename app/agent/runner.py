"""
Agent runner — connects to MCP server and runs an AI agent via tool calls.

Supports two MCP transports:
  - SSE (HTTP): used when mcp_url is provided (Docker sandbox runs)
  - stdio: used as fallback when mcp_url is None (local dev/testing)
"""

import asyncio
import json
import os
import logging
from typing import Any

from dotenv import load_dotenv
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

load_dotenv(override=True)
logger = logging.getLogger(__name__)

# stdio fallback params (local dev only)
_STDIO_PARAMS = StdioServerParameters(
    command="uv",
    args=["run", "python", "app/mcp/server.py"],
    env={**os.environ, "PYTHONPATH": "."},
)


async def run_agent_for_task(
    task_description: str,
    mcp_url: str | None = None,
    max_iterations: int = 20,
) -> dict[str, Any]:
    """
    Executes an AI agent for a specific task using the MCP tool interface.

    Args:
        task_description: The task the agent must complete.
        mcp_url: SSE endpoint of the MCP server (e.g. http://localhost:PORT/sse).
                 If None, falls back to stdio transport for local dev.
        max_iterations: Maximum agent reasoning/tool-call loops.

    Returns:
        dict with keys: output_text, tool_calls, error
    """
    openrouter_key = os.getenv("OPENROUTER_API_KEY")
    openai_key = os.getenv("OPENAI_API_KEY")
    api_key = openrouter_key or openai_key
    tool_calls_executed = []

    if not api_key:
        logger.warning("No API key set — running in benchmark evaluation mode.")
        return {
            "output_text": "Agent executed in benchmark evaluation mode.",
            "tool_calls": tool_calls_executed,
            "error": "No API key configured.",
        }

    try:
        from openai import OpenAI

        if openrouter_key:
            base_url = os.getenv("OPENAI_BASE_URL", "https://openrouter.ai/api/v1")
            model_name = os.getenv("MODEL_NAME", "openai/gpt-4o-mini")
            client = OpenAI(
                api_key=openrouter_key,
                base_url=base_url,
                default_headers={
                    "HTTP-Referer": "https://agentforge.local",
                    "X-Title": "AgentForge Platform",
                },
            )
            logger.info(f"Using OpenRouter model: {model_name}")
        else:
            base_url = os.getenv("OPENAI_BASE_URL")
            model_name = os.getenv("MODEL_NAME", "gpt-4o-mini")
            client = OpenAI(api_key=openai_key, base_url=base_url) if base_url else OpenAI(api_key=openai_key)
            logger.info(f"Using OpenAI model: {model_name}")

        # Choose MCP transport: SSE (Docker sandbox) or stdio (local dev)
        if mcp_url:
            logger.info(f"Connecting to MCP server via SSE at {mcp_url}")
            context = _sse_session(mcp_url)
        else:
            logger.info("Connecting to MCP server via stdio (local dev mode)")
            context = _stdio_session()

        async with context as session:
            await session.initialize()
            tools_result = await session.list_tools()

            openai_tools = [
                {
                    "type": "function",
                    "function": {
                        "name": tool.name,
                        "description": tool.description or "",
                        "parameters": tool.inputSchema,
                    },
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
            max_tokens = int(os.getenv("MAX_TOKENS", "1000"))

            for iteration in range(max_iterations):
                response = client.chat.completions.create(
                    model=model_name,
                    messages=messages,
                    tools=openai_tools,
                    max_tokens=max_tokens,
                )

                msg = response.choices[0].message
                messages.append(msg.model_dump())

                if not msg.tool_calls:
                    final_output = msg.content or "Task completed."
                    break

                for tool_call in msg.tool_calls:
                    tool_name = tool_call.function.name
                    try:
                        args = json.loads(tool_call.function.arguments)
                    except Exception:
                        args = {}

                    try:
                        result = await session.call_tool(tool_name, args)
                        success = True
                        if isinstance(result.content, list):
                            content = [
                                item.text if hasattr(item, "text") else str(item)
                                for item in result.content
                            ]
                        else:
                            content = str(result.content)
                    except Exception as te:
                        success = False
                        content = str(te)

                    tool_calls_executed.append({
                        "name": tool_name,
                        "arguments": args,
                        "result": content,
                        "success": success,
                    })

                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": json.dumps(content, default=str),
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


def _stdio_session():
    """Context manager for stdio MCP transport (local dev)."""
    from contextlib import asynccontextmanager

    @asynccontextmanager
    async def _ctx():
        async with stdio_client(_STDIO_PARAMS) as (read, write):
            async with ClientSession(read, write) as session:
                yield session

    return _ctx()


def _sse_session(mcp_url: str):
    """Context manager for SSE MCP transport (Docker sandbox)."""
    from contextlib import asynccontextmanager
    from mcp.client.sse import sse_client

    @asynccontextmanager
    async def _ctx():
        async with sse_client(mcp_url) as (read, write):
            async with ClientSession(read, write) as session:
                yield session

    return _ctx()


if __name__ == "__main__":
    test_task = "Find all open or pending tickets belonging to customers with overdue invoices and assign to Billing."
    res = asyncio.run(run_agent_for_task(test_task))
    print("Agent Result:", res)
