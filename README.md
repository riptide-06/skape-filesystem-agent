# Skape filesystem agent

The first working reference agent I built and published for Skape, the AI agent marketplace from Securili. It is an OpenAI Agents SDK assistant that reads local files through the Model Context Protocol (MCP) filesystem server, packaged so that it runs cleanly inside a sandboxed marketplace deployment.

## What it does

`main.py` starts the MCP filesystem server (`@modelcontextprotocol/server-filesystem`) over stdio with `npx`, scoped to the `sample_files/` folder, then runs three prompts through an Agents SDK `Agent`:

1. list the files it can read;
2. read `favorite_books.txt` and name the number one book;
3. read `favorite_songs.txt` and suggest one new song.

Each run is traced, and the trace URL is printed at startup.

## What I built

The agent logic starts from the `filesystem_example` in `openai/openai-agents-python`. My work is the hardening a marketplace sandbox needs, all of it in `main.py`:

- a 30 second MCP session timeout, because the first `npx -y` on a cold sandbox downloads the server package and blows past the SDK's 5 second default, which killed the init handshake;
- startup checks for `npx` on PATH and for `OPENAI_API_KEY`, each exiting with a one line message;
- clean handling of 401 (rejected key), 429 (no quota), and network egress failures instead of tracebacks, so an orchestrator sees a single explanatory line.

`SKAPE_UPLOAD_NOTES.txt` records what to upload, the runtime and environment variables, and the sandbox flags to watch: Node absent from the template, the cold `npx` timeout, the two egress destinations, the filesystem scope, and the non-interactive run.

## How it was verified

Run locally on Python 3.13 and Node 25 with `openai-agents==0.18.0`. The MCP server connection was verified end to end. The paid model call was intentionally not exercised during packaging, and the notes say so.

## How to run

Requirements: Python 3.10 or newer, Node.js (for `npx`), and an `OPENAI_API_KEY` on a funded project.

```bash
pip install -r requirements.txt
npm install -g @modelcontextprotocol/server-filesystem   # optional, removes the cold-start download
export OPENAI_API_KEY=...
python main.py
```

Set `OPENAI_AGENTS_DISABLE_TRACING=1` to stop the SDK from posting traces to OpenAI.
