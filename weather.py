from typing import Any
from mcp.server.fastmcp import FastMCP
import mcp.types as types
import os
from runloop_api_client import Runloop
import json
from runloop_setup import setup_devbox

# Initialize FastMCP server
mcp = FastMCP(
    "code-understanding",
    instructions="You are a helpful assistant that has access to a devbox with a codebase, and the tools to set up a devbox if needed. You should use the devbox with the codebase to answer questions about it.",
    settings={"capabilities": {"prompts": {"listChanged": True}}},
)

runloop_client = Runloop(bearer_token=os.environ.get("RUNLOOP_API_KEY"))
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

running_devboxes: dict[str, dict[str, Any]] = {}


# Helper functions for paths. The devbox is intended to bepre-configured with the repo in /home/user/{repo_name}.
def get_repo_path(repo_name: str):
    return f"/home/user/{repo_name}"


def get_generated_repo_map_path(repo_name: str):
    return f"{get_repo_path(repo_name)}/generated_repo_map.txt"


def get_kit_file_tree_path(repo_name: str):
    return f"{get_repo_path(repo_name)}/kit_file_tree.txt"


def get_generated_repo_map_cmd(repo_name: str):
    return f"cd {get_repo_path(repo_name)} && aider --model o3-mini --api-key openai={OPENAI_API_KEY} --yes-always --no-gitignore --show-repo-map > {get_generated_repo_map_path(repo_name)}"


# Public devbox setup.
async def setup_devbox_with_code_mount(github_repo_link: str):
    repo_name = github_repo_link.split("/")[-1]
    # check if snapshot exists, if so create a new devbox from it
    snapshots_list = runloop_client.devboxes.list_disk_snapshots(
        extra_query={"search": "runloop-example-code-understanding-with-mcp"}
    )
    dbx_name = f"/{repo_name}/mcp-understanding-devbox"

    if (
        snapshots_list
        and len(snapshots_list.snapshots) > 0
        and snapshots_list.snapshots[0].name
        == "runloop-example-code-understanding-with-mcp"
    ):

        snapshot = snapshots_list.snapshots[0]
        dbx = runloop_client.devboxes.create_and_await_running(
            snapshot_id=snapshot.id, name=dbx_name
        )
    else:
        print("No snapshot found, setting up new devbox")
        dbx = setup_devbox(dbx_name)
        print(f"Devbox created: {dbx}")

    print(f"Cloning repo {github_repo_link}")
    # Clone the repo
    runloop_client.devboxes.execute_sync(
        dbx.id,
        command=f"git clone https://github:{os.environ.get('GH_TOKEN')}@github.com/{github_repo_link.split('github.com/')[-1]}",
    )

    # Generate the repo map
    runloop_client.devboxes.execute_sync(
        dbx.id,
        command=f"cd {get_repo_path(repo_name)} && aider --model o3-mini --api-key openai={OPENAI_API_KEY} --yes-always --no-gitignore --show-repo-map > {get_generated_repo_map_path(repo_name)}",
    )

    return dbx


# Launch a devbox with the code mount.
async def launch_devbox_with_code_mount(github_repo_link: str):
    if github_repo_link in running_devboxes:
        print(f"Devbox for {github_repo_link} already running")
        return running_devboxes[github_repo_link]
    else:
        print(f"Setting up devbox for {github_repo_link}")
        dbx = await setup_devbox_with_code_mount(github_repo_link)
        repo_name = github_repo_link.split("/")[-1]
        repo_owner = github_repo_link.split("/")[-2]
        running_devboxes[github_repo_link] = {
            "id": dbx.id,
            "repo_map_path": get_generated_repo_map_path(repo_name),
            "file_tree_path": get_kit_file_tree_path(repo_name),
            "repo_name": repo_name,
            "repo_owner": repo_owner,
        }
        return running_devboxes[github_repo_link]


@mcp.prompt()
async def basic_code_understanding(github_link: str, query: str):
    return types.GetPromptResult(
        messages=[
            types.PromptMessage(
                role="user",
                content=types.TextContent(
                    type="text",
                    text=f"Use code understanding tools on the github repo {github_link} and using the repo map and possibly the file tree, answer the question: {query}. You have the tool execute_command_on_devbox to execute shell commands on the devbox.",
                ),
            )
        ]
    )


@mcp.prompt()
async def static_code_understanding(github_link: str, query: str):
    return types.GetPromptResult(
        messages=[
            types.PromptMessage(
                role="user",
                content=types.TextContent(
                    type="text",
                    text=f"Use code understanding tools on the github repo {github_link} and repo map for it",
                ),
            ),
            types.PromptMessage(
                role="user",
                content=types.TextContent(
                    type="text",
                    text=f"You have access to the tools run_kit_cli_get_file_tree, run_kit_cli_extract_symbols, and semantic_code_search. Parse the query: {query} and use the best tool or combination of tools to answer the question. If required, pass {github_link} to the tools.",
                ),
            ),
        ]
    )


@mcp.prompt()
async def historical_code_understanding(github_link: str, query: str):
    return types.GetPromptResult(
        messages=[
            types.PromptMessage(
                role="user",
                content=types.TextContent(
                    type="text",
                    text=f"Use code understanding tools on the github repo {github_link} and repo map for it",
                ),
            ),
            types.PromptMessage(
                role="user",
                content=types.TextContent(
                    type="text",
                    text=f"Using the tool github_history_semantic_search, which returns relevant files to the query: {query}, respond to the query: {query} using the most relevant files. If required, pass {github_link} to the tools.",
                ),
            ),
        ]
    )


@mcp.prompt()
async def dynamic_code_understanding(github_link: str, query: str):
    return types.GetPromptResult(
        messages=[
            types.PromptMessage(
                role="user",
                content=types.TextContent(
                    type="text",
                    text=f"Use code understanding tools on the github repo {github_link} and repo map for it",
                ),
            ),
            types.PromptMessage(
                role="user",
                content=types.TextContent(
                    type="text",
                    text=f"Using the tool run_pytest_call_trace, which returns the call trace for a specific Python test, respond to the query: {query} after running relevant tests. A relevant test is one that is related to the query and exists as a .py file in the repo. If there are no relevant tests, respond with 'No relevant tests found'.",
                ),
            ),
        ]
    )


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


async def generate_repo_map(github_link: str):
    devbox_info = await launch_devbox_with_code_mount(github_link)
    devbox_id = devbox_info["id"]
    repo_map_path = devbox_info["repo_map_path"]
    repo_name = devbox_info["repo_name"]
    # Check if repo map exists, if not generate it
    check_file_cmd = f"test -f {repo_map_path} && echo 'exists' || echo 'not found'"
    check_result = runloop_client.devboxes.execute_sync(
        devbox_id, command=check_file_cmd
    )

    if "not found" in check_result.stdout:
        # Generate the repo map
        runloop_client.devboxes.execute_sync(
            devbox_id, command=get_generated_repo_map_cmd(repo_name)
        )

    # Read and return the repo map contents
    cat_cmd = f"cat {repo_map_path}"
    result = runloop_client.devboxes.execute_sync(devbox_id, command=cat_cmd)
    repo_map = result.stdout
    return repo_map


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
    result = runloop_client.devboxes.execute_sync(
        devbox_id,
        command=f"cd {get_repo_path(repo_name)} && python /home/user/kit_cli.py file-tree > {file_tree_path} && cat {file_tree_path}",
    )
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
    cmd = (
        f"cd {get_repo_path(repo_name)} && python /home/user/kit_cli.py extract-symbols"
    )
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
    result = runloop_client.devboxes.execute_sync(
        devbox_id,
        command=f'cd {get_repo_path(repo_name)} && python /home/user/kit_cli.py semantic-code-search --query "{query}" --top_k {top_k}',
    )
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
    result = runloop_client.devboxes.execute_sync(
        devbox_id,
        command=f'cd {get_repo_path(repo_name)} && python /home/user/gh_cli.py semantic-search --query "{query}" --top_k {top_k}',
    )
    return result.stdout


@mcp.tool()
async def run_pytest_call_trace(github_link: str, test_file: str):
    """
    Run traced_pytest_cli.py in the devbox to get the call trace for a specific Python test.
    Args:
        github_link: Link to the GitHub repository
        test_file: The name of the test function to trace (e.g., test_my_feature)
    Returns:
        The call trace output as a string.
    """
    devbox_info = await launch_devbox_with_code_mount(github_link)
    devbox_id = devbox_info["id"]
    repo_name = devbox_info["repo_name"]
    # Run traced_pytest_cli.py with pytest to run the specific test
    cmd = f"cd {get_repo_path(repo_name)} && python /home/user/traced_pytest_cli.py --trace-package {test_file}"
    result = runloop_client.devboxes.execute_sync(devbox_id, command=cmd)
    return result.stdout


if __name__ == "__main__":
    # Initialize and run the server
    mcp.run(transport="stdio")
