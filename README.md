# A Simple MCP Server written in Python, running remotely via Runloop devboxes

See the [Quickstart](https://modelcontextprotocol.io/quickstart) tutorial for more information.

## Overview

This project implements a Model Context Protocol (MCP) server for code understanding and repository analysis. It provides tools for semantic search over GitHub PRs, Python test call tracing, codebase exploration using the `kit_cli` and `gh_cli`, and dynamic `pytest` tracing via `traced_pytest_cli.py`

## Required Environment Variables

Set the following environment variables before running the server:

- `RUNLOOP_API_KEY`: Your Runloop API key (for devbox and remote execution)
- `OPENAI_API_KEY`: Your OpenAI API key (for embeddings)
- `GH_TOKEN`: Your GitHub API token (for accessing private/public repos)

## Configuration Example

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


## Available Tools

- **Semantic Search over PR History**: Search PRs using natural language queries.
- **Python Test Call Tracing**: Trace the call tree of a Python test.
- **Codebase Exploration**: Use `kit_cli` for file tree, symbol extraction, and semantic code search.

---

For more details, see the code and docstrings in `weather.py`, `gh_cli.py`, and `cli/kit_cli.py`.
