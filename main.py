import asyncio
import os
import shutil
import sys

from openai import APIConnectionError, AuthenticationError, RateLimitError

from agents import Agent, Runner, gen_trace_id, trace
from agents.mcp import MCPServer, MCPServerStdio


async def run(mcp_server: MCPServer):
    agent = Agent(
        name="Assistant",
        instructions="Use the tools to read the filesystem and answer questions based on those files.",
        mcp_servers=[mcp_server],
    )

    # List the files it can read
    message = "Read the files and list them."
    print(f"Running: {message}")
    result = await Runner.run(starting_agent=agent, input=message)
    print(result.final_output)

    # Ask about books
    message = "Read favorite_books.txt and tell me my #1 favorite book."
    print(f"\n\nRunning: {message}")
    result = await Runner.run(starting_agent=agent, input=message)
    print(result.final_output)

    # Ask a question that reads then reasons.
    message = "Read favorite_songs.txt and suggest one new song that I might like."
    print(f"\n\nRunning: {message}")
    result = await Runner.run(starting_agent=agent, input=message)
    print(result.final_output)


async def main():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    samples_dir = os.path.join(current_dir, "sample_files")

    async with MCPServerStdio(
        name="Filesystem Server, via npx",
        params={
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-filesystem", samples_dir],
        },
        # Give the stdio MCP server room to start. On a cold sandbox the first
        # `npx -y` invocation downloads the server package, which easily exceeds
        # the SDK's 5s default and kills the init handshake with a timeout.
        client_session_timeout_seconds=30,
    ) as server:
        trace_id = gen_trace_id()
        with trace(workflow_name="MCP Filesystem Example", trace_id=trace_id):
            print(f"View trace: https://platform.openai.com/traces/trace?trace_id={trace_id}\n")
            await run(server)


if __name__ == "__main__":
    # The MCP filesystem server runs via `npx`, so Node.js must be on PATH.
    if not shutil.which("npx"):
        print(
            "ERROR: `npx` was not found on PATH. This example needs a Node.js runtime.\n"
            "Install Node.js (which provides npx), e.g. `apt-get install -y nodejs npm`,\n"
            "or provision a sandbox template that includes Node.",
            file=sys.stderr,
        )
        sys.exit(1)

    if not os.environ.get("OPENAI_API_KEY"):
        print(
            "ERROR: OPENAI_API_KEY is not set. Provision it as an environment variable\n"
            "before running (do not hardcode it into any file).",
            file=sys.stderr,
        )
        sys.exit(1)

    try:
        asyncio.run(main())
    except AuthenticationError:
        print(
            "ERROR: OpenAI rejected the API key (401). Check that OPENAI_API_KEY is\n"
            "valid and belongs to the intended project.",
            file=sys.stderr,
        )
        sys.exit(1)
    except RateLimitError:
        print(
            "ERROR: OpenAI returned a quota/rate-limit error (429). The key is valid but\n"
            "the account/project has no available quota. Add billing/credits and retry.",
            file=sys.stderr,
        )
        sys.exit(1)
    except APIConnectionError:
        print(
            "ERROR: Could not reach OpenAI (network/egress failure). In a locked-down\n"
            "sandbox, ensure outbound HTTPS to api.openai.com is allowed. The npm\n"
            "registry (registry.npmjs.org) must also be reachable unless the MCP server\n"
            "package is pre-installed.",
            file=sys.stderr,
        )
        sys.exit(1)
