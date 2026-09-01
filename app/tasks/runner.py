import asyncio
import json
import os

from dotenv import load_dotenv
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from openai import OpenAI


load_dotenv()


server_params = StdioServerParameters(
    command="uv",
    args=[
        "run",
        "python",
        "app/mcp/server.py",
    ],
    env={
        **os.environ,
        "PYTHONPATH": ".",
    },
)


TASK = """
Find all open or pending tickets belonging to customers who have
overdue invoices.

Find which of those tickets are not assigned to the Billing team.

Assign those tickets to the Billing team.

Use the available tools.
Do not assume IDs.
Do not modify tickets that are already assigned to Billing.
Verify that every required ticket was successfully updated.
"""


async def run_agent() -> None:
    """
    Start the MCP server, give the task to the AI agent,
    execute its requested tool calls, and continue until
    the agent finishes.
    """

    client = OpenAI()

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:

            # Initialize MCP connection.
            await session.initialize()

            # Discover available MCP tools.
            tools_result = await session.list_tools()

            openai_tools = []

            for tool in tools_result.tools:
                openai_tools.append(
                    {
                        "type": "function",
                        "name": tool.name,
                        "description": tool.description or "",
                        "parameters": tool.inputSchema,
                    }
                )

            messages = [
                {
                    "role": "system",
                    "content": (
                        "You are an AI agent operating inside "
                        "the AgentArena environment. "
                        "Use the available tools to complete "
                        "the task. "
                        "Do not invent information. "
                        "Continue using tools until the task "
                        "is completely finished."
                    ),
                },
                {
                    "role": "user",
                    "content": TASK,
                },
            ]

            print("\nStarting agent...\n")

            max_iterations = 20

            for iteration in range(max_iterations):

                response = client.responses.create(
                    model="gpt-4o-mini",
                    input=messages,
                    tools=openai_tools,
                )

                # Find tool calls requested by the model.
                tool_calls = [
                    item
                    for item in response.output
                    if item.type == "function_call"
                ]

                # No tool calls means the agent is finished.
                if not tool_calls:
                    print("\nAgent finished:")
                    print(response.output_text)
                    return

                # Execute every requested tool call.
                for tool_call in tool_calls:

                    print(
                        f"\nAgent wants to call: "
                        f"{tool_call.name}"
                    )

                    print(
                        f"Arguments: "
                        f"{tool_call.arguments}"
                    )

                    arguments = json.loads(
                        tool_call.arguments
                    )

                    # Call the MCP tool.
                    result = await session.call_tool(
                        tool_call.name,
                        arguments,
                    )

                    print(
                        f"Tool result: "
                        f"{result.content}"
                    )

                    # Add the model's tool call to the
                    # conversation history.
                    messages.append(
                        {
                            "type": "function_call",
                            "call_id": tool_call.call_id,
                            "name": tool_call.name,
                            "arguments": tool_call.arguments,
                        }
                    )

                    # Add the tool's result to the
                    # conversation history.
                    messages.append(
                        {
                            "type": "function_call_output",
                            "call_id": tool_call.call_id,
                            "output": json.dumps(
                                result.content,
                                default=str,
                            ),
                        }
                    )

            print(
                "\nAgent stopped: "
                "maximum iterations reached."
            )


async def main():
    """
    Standalone entry point.

    This allows:
        uv run python app/agent/runner.py

    while app/tasks/runner.py can import:
        from app.agent.runner import run_agent
    """

    await run_agent()


if __name__ == "__main__":
    asyncio.run(main())