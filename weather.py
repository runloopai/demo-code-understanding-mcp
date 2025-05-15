from typing import Any
from mcp.server.fastmcp import FastMCP
import mcp.types as types
import os
from runloop_api_client import Runloop
import json

# Define available prompts
PROMPTS = {
    "semantic-pr-search": types.Prompt(
        name="semantic-pr-search",
        description="Search GitHub pull requests using a natural language query.",
        arguments=[
            types.PromptArgument(
                name="query",
                description="Natural language search query",
                required=True
            ),
            types.PromptArgument(
                name="top_k",
                description="Number of top results to return",
                required=False
            ),
        ],
    ),
    "python-test-call-trace": types.Prompt(
        name="python-test-call-trace",
        description="Trace the function call tree of a specific Python test.",
        arguments=[
            types.PromptArgument(
                name="test_name",
                description="Name of the test function to trace (e.g., test_my_feature)",
                required=True
            ),
            types.PromptArgument(
                name="github_link",
                description="GitHub repository link (if using devbox)",
                required=True
            ),
        ],
    ),
    "kit-file-tree": types.Prompt(
        name="kit-file-tree",
        description="Show the file tree of a repository using kit_cli.",
        arguments=[
            types.PromptArgument(
                name="github_link",
                description="GitHub repository link",
                required=True
            ),
        ],
    ),
    "kit-extract-symbols": types.Prompt(
        name="kit-extract-symbols",
        description="Extract code symbols from a repository or file using kit_cli.",
        arguments=[
            types.PromptArgument(
                name="github_link",
                description="GitHub repository link",
                required=True
            ),
            types.PromptArgument(
                name="file",
                description="Optional file path (relative to repo root) to extract symbols from",
                required=False
            ),
        ],
    ),
    "kit-semantic-code-search": types.Prompt(
        name="kit-semantic-code-search",
        description="Perform semantic code search over a repository using kit_cli.",
        arguments=[
            types.PromptArgument(
                name="github_link",
                description="GitHub repository link",
                required=True
            ),
            types.PromptArgument(
                name="query",
                description="Natural language search query",
                required=True
            ),
            types.PromptArgument(
                name="top_k",
                description="Number of top results to return",
                required=False
            ),
        ],
    ),
}

# Initialize FastMCP server
mcp = FastMCP("code-understanding")

@ mcp.list_prompts()
async def list_prompts() -> list[types.Prompt]:
    return list(PROMPTS.values())

@ mcp.get_prompt()
async def get_prompt(name: str, arguments: dict[str, str] | None = None) -> types.GetPromptResult:
    if name not in PROMPTS:
        raise ValueError(f"Prompt not found: {name}")
    # Example: just echo the arguments in the prompt message
    args = arguments or {}
    if name == "semantic-pr-search":
        query = args.get("query", "")
        top_k = args.get("top_k", "5")
        return types.GetPromptResult(
            messages=[
                types.PromptMessage(
                    role="user",
                    content=types.TextContent(
                        type="text",
                        text=f"Search GitHub PRs for: {query}\nReturn top {top_k} results."
                    )
                )
            ]
        )
    if name == "python-test-call-trace":
        test_name = args.get("test_name", "")
        github_link = args.get("github_link", "")
        return types.GetPromptResult(
            messages=[
                types.PromptMessage(
                    role="user",
                    content=types.TextContent(
                        type="text",
                        text=f"Trace the call tree for test '{test_name}' in repo {github_link}."
                    )
                )
            ]
        )
    if name == "kit-file-tree":
        github_link = args.get("github_link", "")
        return types.GetPromptResult(
            messages=[
                types.PromptMessage(
                    role="user",
                    content=types.TextContent(
                        type="text",
                        text=f"Show the file tree for repo {github_link}."
                    )
                )
            ]
        )
    if name == "kit-extract-symbols":
        github_link = args.get("github_link", "")
        file = args.get("file", None)
        file_part = f" in file {file}" if file else ""
        return types.GetPromptResult(
            messages=[
                types.PromptMessage(
                    role="user",
                    content=types.TextContent(
                        type="text",
                        text=f"Extract code symbols from repo {github_link}{file_part}."
                    )
                )
            ]
        )
    if name == "kit-semantic-code-search":
        github_link = args.get("github_link", "")
        query = args.get("query", "")
        top_k = args.get("top_k", "5")
        return types.GetPromptResult(
            messages=[
                types.PromptMessage(
                    role="user",
                    content=types.TextContent(
                        type="text",
                        text=f"Semantic code search in repo {github_link} for: {query}\nReturn top {top_k} results."
                    )
                )
            ]
        )
    raise ValueError("Prompt implementation not found")

runloop_client = Runloop(bearer_token=os.environ.get("RUNLOOP_API_KEY"))
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

running_devboxes: dict[str, dict[str, Any]] = {}

# Helper functions for paths
def get_repo_path(repo_name: str):
    return f"/home/user/{repo_name}"

def get_generated_repo_map_path(repo_name: str):
    return f"{get_repo_path(repo_name)}/generated_repo_map.txt"

def get_kit_file_tree_path(repo_name: str):
    return f"{get_repo_path(repo_name)}/kit_file_tree.txt"

def get_generated_repo_map_cmd(repo_name: str):
    return f"cd {get_repo_path(repo_name)} && \
      wget -qO- https://aider.chat/install.sh | sh && \
      export PATH=$PATH:~/.local/bin && \
      aider --model o3-mini --api-key openai={OPENAI_API_KEY} --yes-always --no-gitignore --show-repo-map > {get_generated_repo_map_path(repo_name)}"

# Public devbox
async def setup_devbox_with_code_mount(github_repo_link: str):
    repo_name = github_repo_link.split("/")[-1]
    repo_owner = github_repo_link.split("/")[-2]

    shared_name = f"{repo_owner}-{repo_name}-initial-setup"
    # check if devbox exists
    devboxes_list = runloop_client.devboxes.list(extra_query={"search": shared_name}, status="running")
    if devboxes_list and len(devboxes_list.devboxes) > 0:
        return devboxes_list.devboxes[0]

    # check if snapshot exists
    snapshots_list = runloop_client.devboxes.list_disk_snapshots(extra_query={"search": shared_name})
    if snapshots_list and len(snapshots_list.snapshots) > 0:
        snapshot = snapshots_list.snapshots[0]
        dbx = runloop_client.devboxes.create_and_await_running(snapshot_id=snapshot.id)
        return dbx

    # create new devbox
    dbx = runloop_client.devboxes.create_and_await_running(
        code_mounts=[{
            "repo_name": repo_name,
            "repo_owner": repo_owner,
        }],
        launch_parameters={
            "launch_commands": [
                "sudo apt-get update",
                "sudo apt-get install -y libsqlite3-dev",
                "pip install --user cased-kit openai chromadb",
            ]
        },
        environment_variables={
            "OPENAI_API_KEY": os.environ.get("OPENAI_API_KEY"),
            "GH_TOKEN": os.environ.get("GH_TOKEN")
        },
        metadata={
            "repo_name": repo_name,
            "repo_owner": repo_owner,
            "github_repo_link": github_repo_link
        }
    )
    runloop_client.devboxes.write_file_contents(dbx.id, file_path="/home/user/kit_cli.py", contents=open("cli/kit_cli.py", "r").read())
    runloop_client.devboxes.write_file_contents(dbx.id, file_path="/home/user/gh_cli.py", contents=open("cli/gh_cli.py", "r").read())
    runloop_client.devboxes.write_file_contents(dbx.id, file_path="/home/user/traced_pytest_cli.py", contents=open("cli/traced_pytest_cli.py", "r").read())
    # Create a snapshot with descriptive name and metadata using snapshot_disk
    snapshot_description = f"Initial setup for repo {repo_owner}/{repo_name} from {github_repo_link}"
    snapshot_metadata = {
        "repo_name": repo_name,
        "repo_owner": repo_owner,
        "github_repo_link": github_repo_link,
        "description": snapshot_description
    }
    snapshot = runloop_client.devboxes.snapshot_disk(
        dbx.id,
        name=shared_name,
        description=snapshot_description,
        metadata=snapshot_metadata
    )
    return dbx

async def launch_devbox_with_code_mount(github_repo_link: str):
    if github_repo_link in running_devboxes:
        return running_devboxes[github_repo_link]
    else:
        dbx = await setup_devbox_with_code_mount(github_repo_link)
        repo_name = github_repo_link.split("/")[-1]
        repo_owner = github_repo_link.split("/")[-2]
        running_devboxes[github_repo_link] = {
            "id": dbx.id,
            "repo_map_path": get_generated_repo_map_path(repo_name),
            "file_tree_path": get_kit_file_tree_path(repo_name),
            "repo_name": repo_name,
            "repo_owner": repo_owner
        }
        return running_devboxes[github_repo_link]

async def generate_repo_map(github_link: str):
    devbox_info = await launch_devbox_with_code_mount(github_link)
    devbox_id = devbox_info["id"]
    repo_map_path = devbox_info["repo_map_path"]
    repo_name = devbox_info["repo_name"]
    # Check if repo map exists, if not generate it
    check_file_cmd = f"test -f {repo_map_path} && echo 'exists' || echo 'not found'"
    check_result = runloop_client.devboxes.execute_sync(devbox_id, command=check_file_cmd)
    
    if "not found" in check_result.stdout:
        # Generate the repo map
        runloop_client.devboxes.execute_sync(devbox_id, command=get_generated_repo_map_cmd(repo_name))
    
    # Read and return the repo map contents
    cat_cmd = f"cat {repo_map_path}"
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
    devbox_info = await launch_devbox_with_code_mount(github_link)
    devbox_id = devbox_info["id"]
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
    devbox_info = await launch_devbox_with_code_mount(github_link)
    devbox_id = devbox_info["id"]
    repo_name = devbox_info["repo_name"]
    file_tree_path = devbox_info["file_tree_path"]
    result = runloop_client.devboxes.execute_sync(devbox_id, command=f"cd {get_repo_path(repo_name)} && python /home/user/kit_cli.py file-tree > {file_tree_path} && cat {file_tree_path}")
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
    devbox_info = await launch_devbox_with_code_mount(github_link)
    devbox_id = devbox_info["id"]
    repo_name = devbox_info["repo_name"]
    cmd = f"cd {get_repo_path(repo_name)} && python /home/user/kit_cli.py extract-symbols"
    if file:
        cmd += f" --file {file}"
    result = runloop_client.devboxes.execute_sync(devbox_id, command=cmd)
    symbols = result.stdout
    return symbols

@mcp.tool()
async def semantic_code_search(github_link: str, query: str, top_k: int = 5):
    """
    Perform semantic search over a code repository using OpenAI embeddings.
    Args:
        repo_path: Path to the local code repository
        query: Natural language search query
        top_k: Number of top results to return
    Returns:
        List of top matching code snippets with file and score.
    """
    devbox_info = await launch_devbox_with_code_mount(github_link)
    devbox_id = devbox_info["id"]
    repo_name = devbox_info["repo_name"]
    result = runloop_client.devboxes.execute_sync(devbox_id, command=f"cd {get_repo_path(repo_name)} && python /home/user/kit_cli.py semantic-code-search --query \"{query}\" --top_k {top_k}")
    return result.stdout

@mcp.tool()
async def github_history_semantic_search(github_link: str, query: str, top_k: int = 1):
    """
    Perform semantic search over the GitHub PR history embedding using ChromaDB.
    Args:
        github_link: GitHub repo in the form owner/repo
        query: Natural language search query
        top_k: Number of top results to return
        collection: ChromaDB collection name (default: github_prs)
    Returns:
        JSON string of top matching PRs with metadata and score.
    """
    devbox_info = await launch_devbox_with_code_mount(github_link)
    devbox_id = devbox_info["id"]
    repo_name = devbox_info["repo_name"]
    result = runloop_client.devboxes.execute_sync(devbox_id, command=f"cd {get_repo_path(repo_name)} && python /home/user/gh_cli.py semantic-search --query \"{query}\" --top_k {top_k}")
    return result.stdout

@mcp.tool()
async def run_pytest_call_trace(github_link: str, test_name: str):
    """
    Run traced_pytest_cli.py in the devbox to get the call trace for a specific Python test.
    Args:
        github_link: Link to the GitHub repository
        test_name: The name of the test function to trace (e.g., test_my_feature)
    Returns:
        The call trace output as a string.
    """
    devbox_info = await launch_devbox_with_code_mount(github_link)
    devbox_id = devbox_info["id"]
    repo_name = devbox_info["repo_name"]
    # Run traced_pytest_cli.py with pytest to run the specific test
    cmd = f"cd {get_repo_path(repo_name)} && python /home/user/traced_pytest_cli.py --trace-package {test_name}"
    result = runloop_client.devboxes.execute_sync(devbox_id, command=cmd)
    return result.stdout


if __name__ == "__main__":
    # Initialize and run the server
    mcp.run(transport='stdio')