# A Simple MCP Weather Server written in Python

See the [Quickstart](https://modelcontextprotocol.io/quickstart) tutorial for more information.

## Overview

This project implements a Model Context Protocol (MCP) server for code understanding and repository analysis. It provides tools for semantic search over GitHub PRs, Python test call tracing, and codebase exploration using the `kit_cli` utility, 

## Required Environment Variables

Set the following environment variables before running the server:

- `RUNLOOP_API_KEY`: Your Runloop API key (for devbox and remote execution)
- `OPENAI_API_KEY`: Your OpenAI API key (for embeddings)
- `GH_TOKEN`: Your GitHub API token (for accessing private/public repos)

## kit_cli Utility

The `kit_cli` is a command-line tool for repository analysis, supporting:
- **file-tree**: Outputs the file tree of the repository
- **extract-symbols**: Extracts code symbols from the repository or a specific file
- **semantic-code-search**: Performs semantic code search using OpenAI embeddings

Example usage:
```bash
python cli/kit_cli.py file-tree --repo_path /path/to/repo
python cli/kit_cli.py extract-symbols --repo_path /path/to/repo [--file relative/path/to/file.py]
python cli/kit_cli.py semantic-code-search --repo_path /path/to/repo --query "search term" --top_k 5
```

## Running the MCP Server

1. Install dependencies and set environment variables as above.
2. Start the server:
   ```bash
   python weather.py
   ```

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

## Available Tools

- **Semantic Search over PR History**: Search PRs using natural language queries.
- **Python Test Call Tracing**: Trace the call tree of a Python test.
- **Codebase Exploration**: Use `kit_cli` for file tree, symbol extraction, and semantic code search.

---

For more details, see the code and docstrings in `weather.py`, `gh_cli.py`, and `cli/kit_cli.py`.
