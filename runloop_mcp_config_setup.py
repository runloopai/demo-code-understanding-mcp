import json
import os


def add_mcp_server_entry(config_path: str, server_name: str, new_entry: dict):
    # Read the existing config
    with open(config_path, "r") as f:
        config = json.load(f)

    # Add the new entry to mcpServers
    if server_name not in config["mcpServers"]:
        config["mcpServers"][server_name] = new_entry
    else:
        raise Exception(f"Server {server_name} already exists in mcpServers")

    # Write back the updated config
    with open(config_path, "w") as f:
        json.dump(config, f, indent=2)


if __name__ == "__main__":
    # Path to the config file
    config_path = os.path.expanduser(
        "~/Library/Application Support/Claude/claude_desktop_config.json"
    )

    OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "YOUR_OPENAI_API_KEY")
    GH_TOKEN = os.environ.get("GH_TOKEN", "YOUR_GH_TOKEN")
    RUNLOOP_API_KEY = os.environ.get("RUNLOOP_API_KEY", "YOUR_RUNLOOP_API_KEY")

    # The new server entry you want to add
    new_server_entry = {
        "command": "PATH TO UV/PYTHON ENVIRONMENT",
        "args": ["--directory", "PATH TO DEMO REPO", "run", "weather.py"],
        "env": {
            "RUNLOOP_API_KEY": RUNLOOP_API_KEY,
            "OPENAI_API_KEY": OPENAI_API_KEY,
            "GH_TOKEN": GH_TOKEN,
        },
    }

    # Name for the new server entry
    server_name = "code-understanding"

    try:
        add_mcp_server_entry(config_path, server_name, new_server_entry)
        print(f"Successfully added {server_name} to mcpServers")
    except Exception as e:
        print(f"Error updating config: {str(e)}")
