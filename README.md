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
      "args": ["--directory", "/CURRENT_FOLDER_PATH", "run", "rl_mcp.py"],
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

Running `runloop_snapshot_setup.py` to add a fully configured snapshot to your account. The snapshot will have all the required libraries for the MCP server to operate on your repository. Running the MCP without this setup step will still work as expected, it may take a few moments longer for a new devbox to be set up with the required libraries before a command can fully execute.

We use Claude internally to connect to MCP servers. If the server is configured correctly, tools should be available in the Claude Desktop client and 4 prompts will be available as templates for accessing information about your repo via Claude Desktop.


## Available Tools

- **Historical context**: Search PRs using natural language queries, via `cli/gh_cli.py`.
- **Dynamic context**: Trace the call tree of a Python test and follow the execution dynamically, via `cli/traced_pytest_cli.py`
- **Static context**: Use `cli/kit_cli.py` for file tree, symbol extraction, and semantic code search.

---

For more details, read the code and docstrings (or deploy this MCP on this repo!).
