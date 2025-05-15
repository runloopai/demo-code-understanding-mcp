# A Simple MCP Server written in Python, running remotely via Runloop devboxes

See the [Quickstart](https://modelcontextprotocol.io/quickstart) tutorial for more information.

## Overview

This project implements a Model Context Protocol (MCP) server for code understanding and repository analysis. It provides tools for semantic search over GitHub PRs, Python test call tracing, codebase exploration using the `kit_cli` and `gh_cli`, and dynamic `pytest` tracing via `traced_pytest_cli.py`

## Required Environment Variables

Set the following environment variables before running commands:

- `RUNLOOP_API_KEY`: Your Runloop API key (for devbox and remote execution)
- `OPENAI_API_KEY`: Your OpenAI API key (for embeddings)
- `GH_TOKEN`: Your GitHub API token (for accessing private/public repos)

## Configuration Example

Run `runloop_mcp_config_setup.py` locally to add the mcp config to your `claude_desktop_config.json` OR

See `example_claude_desktop_config.json` for a sample configuration to launch the MCP server with the required environment variables:

```json
{
  "mcpServers": {
    "code-understanding": {
      "command": "/PATH_TO_YOUR_VENV/bin/uv",
      "args": ["--directory", "/CURRENT_FOLDER_PATH", "run", "weather.py"],
      "env": {
        "RUNLOOP_API_KEY": "YOUR_RUNLOOP_API_KEY",
        "OPENAI_API_KEY": "YOUR_OPENAI_API_KEY",
        "GH_TOKEN": "YOUR_GH_TOKEN"
      }
    }
  }
}
```
See [https://modelcontextprotocol.io/quickstart/user](https://modelcontextprotocol.io/quickstart/user) for how to connect this MCP to your Claude Desktop client!

## Running the mcp server

You can run `runloop_snapshot_setup.py` to add a fully configured snapshot to your account.


## Available Tools

- **Semantic Search over PR History**: Search PRs using natural language queries, via `gh_cli`.
- **Python Test Call Tracing**: Trace the call tree of a Python test, via `cli/traced_pytest_cli.py`
- **Codebase Exploration**: Use `cli/kit_cli` for file tree, symbol extraction, and semantic code search.

---

For more details, read the code and docstrings (or deploy this MCP on this repo!).
