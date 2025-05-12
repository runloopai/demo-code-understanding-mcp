from typing import Any
from mcp.server.fastmcp import FastMCP
import os
from runloop_api_client import Runloop
import json

# Initialize FastMCP server
mcp = FastMCP("code-understanding")

runloop_client = Runloop(bearer_token=os.environ.get("RUNLOOP_API_KEY"))
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY") or "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"

running_devboxes: dict[str, str] = {}
devbox_information: dict[str, dict[str, Any]] = {}

generate_repo_map_cmd = f"cd /home/user/runloop-examples && wget -qO- https://aider.chat/install.sh | sh && touch ./generated_repo_map.txt && aider --model o3-mini --api-key openai={OPENAI_API_KEY} --yes-always --show-repo-map > ./generated_repo_map.txt"

# Public devbox
async def launch_devbox_with_code_mount(github_repo_link: str):
    if github_repo_link in running_devboxes:
        return running_devboxes[github_repo_link]
    else:
        dbx = runloop_client.devboxes.create_and_await_running(
            code_mounts=[{
                "repo_name": github_repo_link.split("/")[-1],
                "repo_owner": github_repo_link.split("/")[-2],
            }],
            launch_parameters={
                "launch_commands": [
                    "sudo apt-get install -y libsqlite3-dev",
                    "pip install cased-kit"
                ]
            }
        )
        runloop_client.devboxes.write_file_contents(dbx.id, file_path="/home/user/kit_cli.py", contents=open("kit_cli.py", "r").read())
        running_devboxes[github_repo_link] = dbx.id
        return dbx.id

async def generate_repo_map(github_link: str):
    devbox_id = await launch_devbox_with_code_mount(github_link)
    # Check if repo map exists, if not generate it
    check_file_cmd = "test -f /home/user/runloop-examples/generated_repo_map.txt && echo 'exists' || echo 'not found'"
    check_result = runloop_client.devboxes.execute_sync(devbox_id, command=check_file_cmd)
    
    if "not found" in check_result.stdout:
        # Generate the repo map
        runloop_client.devboxes.execute_sync(devbox_id, command=generate_repo_map_cmd)
    
    # Read and return the repo map contents
    cat_cmd = "cat /home/user/runloop-examples/generated_repo_map.txt"
    result = runloop_client.devboxes.execute_sync(devbox_id, command=cat_cmd)
    repo_map = result.stdout
    return repo_map

# This allows claude to use the shell of a devbox and interact with the repo.
@mcp.tool()
async def execute_command_on_devbox(github_link: str, command: str):
    """
    Here's a tool that executes a command on a devbox. The devbox is pre-configured with the repo in /home/user/{repo_name}.
    You can use it to execute shell commands on the devbox and learn about the repo.
    
    Args:
        github_link: link to a github repo
        command: command to execute on the devbox
    """
    devbox_id = await launch_devbox_with_code_mount(github_link)
    result = runloop_client.devboxes.execute_sync(devbox_id, command=command)
    return json.dumps(result.model_dump()) 

@mcp.tool()
async def read_repo_map(github_link: str):
    """
    Generate and read the repo map for a github repo to aid in understanding the repo.
    """
    repo_map = await generate_repo_map(github_link)
    
    return repo_map

@mcp.tool()
async def run_kit_cli_get_file_tree(github_link: str):
    """
    Run the kit cli with the file-tree argument to return a json object of the file tree.
    """
    devbox_id = await launch_devbox_with_code_mount(github_link)

    result = runloop_client.devboxes.execute_sync(devbox_id, command="cd /home/user/runloop-examples && python /home/user/kit_cli.py file-tree > ./kit_file_tree.txt && cat ./kit_file_tree.txt")
    file_tree = result.stdout
    return file_tree

@mcp.tool()
async def run_kit_cli_extract_symbols(github_link: str, file: str | None = None):
    """
    Run the kit cli with the extract-symbols argument to return a json object of the symbols.
    
    Args:
        github_link: Link to the GitHub repository
        file: Optional file path relative to repo root to extract symbols from
    """
    devbox_id = await launch_devbox_with_code_mount(github_link)
    
    cmd = "cd /home/user/runloop-examples && python /home/user/kit_cli.py extract-symbols"
    if file:
        cmd += f" --file {file}"
    cmd += " > ./kit_symbols.txt && cat ./kit_symbols.txt"
    
    result = runloop_client.devboxes.execute_sync(devbox_id, command=cmd)
    symbols = result.stdout
    return symbols


### Initialize the server

if __name__ == "__main__":
    # Initialize and run the server
    mcp.run(transport='stdio')