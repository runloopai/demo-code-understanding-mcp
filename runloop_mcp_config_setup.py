import json
import os
import subprocess


def add_mcp_server_entry(config_path: str, server_name: str, new_entry: dict):
    # Read the existing config
    with open(config_path, "r") as f:
        config = json.load(f)

    # Add the new entry to mcpServers
    if server_name not in config["mcpServers"]:
        config["mcpServers"][server_name] = new_entry
    else:
        raise Exception(f"Server {server_name} already exists in mcpServers")

    # Ask for user approval before writing
    print(
        f"About to update {config_path} with the following entry for '{server_name}':"
    )
    print(json.dumps(new_entry, indent=2))
    approval = (
        input("Do you want to proceed with updating the config? [y/N]: ")
        .strip()
        .lower()
    )
    if approval not in ("y", "yes"):
        print("Update cancelled by user.")
        return False

    # Write back the updated config
    with open(config_path, "w") as f:
        json.dump(config, f, indent=2)
    print(f"Config updated successfully: {config_path}")
    return True


def choose_config_path():
    print("Which config do you want to update?")
    print("1. Claude (~/Library/Application Support/Claude/claude_desktop_config.json)")
    print("2. Cursor (~/.cursor/mcp.json)")
    choice = input("Enter 1 for Claude or 2 for Cursor [1/2]: ").strip()
    if choice == "2":
        config_path = os.path.expanduser("~/.cursor/mcp.json")
        config_name = "cursor"
    else:
        config_path = os.path.expanduser(
            "~/Library/Application Support/Claude/claude_desktop_config.json"
        )
        config_name = "claude"
    return config_path, config_name


if __name__ == "__main__":
    # Choose config
    config_path, config_name = choose_config_path()

    OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "YOUR_OPENAI_API_KEY")
    GH_TOKEN = os.environ.get("GH_TOKEN", "YOUR_GH_TOKEN")
    RUNLOOP_API_KEY = os.environ.get("RUNLOOP_API_KEY", "YOUR_RUNLOOP_API_KEY")

    # The new server entry you want to add
    new_server_entry = {
        "command": subprocess.run(
            ["which", "uv"], capture_output=True, text=True
        ).stdout.strip()
        or subprocess.run(
            ["which", "python"], capture_output=True, text=True
        ).stdout.strip(),
        "args": ["--directory", os.getcwd(), "run", "rl_mcp.py"],
        "env": {
            "RUNLOOP_API_KEY": RUNLOOP_API_KEY,
            "OPENAI_API_KEY": OPENAI_API_KEY,
            "GH_TOKEN": GH_TOKEN,
        },
    }

    # Name for the new server entry
    server_name = "code-understanding"

    try:
        updated = add_mcp_server_entry(config_path, server_name, new_server_entry)
        if updated:
            print(f"Successfully added {server_name} to {config_name} config.")
        else:
            print(f"No changes made to {config_name} config.")
    except Exception as e:
        print(f"Error updating config: {str(e)}")
