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
Find customers who have overdue invoices.

For each such customer, find their tickets that are currently
open or pending.

Assign those tickets to the Billing team.

You must inspect the environment using the available tools.
Do not assume IDs.
"""


async def main():
    client = OpenAI()

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

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
                        "the AgentForge environment. "
                        "Use the available tools to complete "
                        "the task. Do not invent information. "
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
                    model="gpt-5",
                    input=messages,
                    tools=openai_tools,
                )

                tool_calls = [
                    item
                    for item in response.output
                    if item.type == "function_call"
                ]

                if not tool_calls:
                    print("\nAgent finished:")
                    print(response.output_text)
                    break

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

                    result = await session.call_tool(
                        tool_call.name,
                        arguments,
                    )

                    print(
                        f"Tool result: {result.content}"
                    )

                    messages.append(
                        {
                            "type": "function_call",
                            "call_id": tool_call.call_id,
                            "name": tool_call.name,
                            "arguments": tool_call.arguments,
                        }
                    )

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

            else:
                print(
                    "\nAgent stopped: "
                    "maximum iterations reached."
                )


if __name__ == "__main__":
    asyncio.run(main())