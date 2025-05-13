from typing import Any
from mcp.server.fastmcp import FastMCP
import os
from runloop_api_client import Runloop
import json
import openai
from kit import Repository

# Initialize FastMCP server
mcp = FastMCP("code-understanding")

runloop_client = Runloop(bearer_token=os.environ.get("RUNLOOP_API_KEY"))
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
openai.api_key = OPENAI_API_KEY

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

# OpenAI embedding function
def openai_embed(texts):
    response = openai.embeddings.create(
        input=texts,
        model="text-embedding-3-small"
    )
    return [record['embedding'] for record in response['data']]

# Public devbox
async def launch_devbox_with_code_mount(github_repo_link: str):
    if github_repo_link in running_devboxes:
        return running_devboxes[github_repo_link]
    else:
        repo_name = github_repo_link.split("/")[-1]
        repo_owner = github_repo_link.split("/")[-2]
        dbx = runloop_client.devboxes.create_and_await_running(
            code_mounts=[{
                "repo_name": repo_name,
                "repo_owner": repo_owner,
            }],
            launch_parameters={
                "launch_commands": [
                    "sudo apt-get update",
                    "sudo apt-get install -y libsqlite3-dev",
                    "pip install cased-kit"
                ]
            }
        )
        runloop_client.devboxes.write_file_contents(dbx.id, file_path="/home/user/kit_cli.py", contents=open("kit_cli.py", "r").read())
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

async def create_embedding_on_devbox(github_link: str, command: str):
    """
    Create an embedding on the devbox and save it as a parquet file.
    
    Args:
        github_link: Link to the GitHub repository
        command: Command to execute on the devbox
    Returns:
        Path to the saved parquet file
    """
    devbox_info = await launch_devbox_with_code_mount(github_link)
    devbox_id = devbox_info["id"]
    repo_name = devbox_info["repo_name"]
    
    # Initialize repo and create embeddings
    repo = Repository(get_repo_path(repo_name))
    repo_index = repo.index(embed_fn=openai_embed)
    
    # Save embeddings to parquet
    parquet_path = f"/home/user/{repo_name}_embeddings.parquet"
    await runloop_client.devboxes.write_file_contents(devbox_id, file_path=parquet_path, contents=repo_index.to_parquet())
    return parquet_path

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
    repo_name = devbox_info["repo_name"]
    
    # Initialize repo and index on devbox
    repo = Repository(get_repo_path(repo_name))
    repo.index(embed_fn=openai_embed)
    
    # Perform semantic search
    results = repo.search_semantic(query=query, top_k=top_k, embed_fn=openai_embed)
    
    return json.dumps(results)

@mcp.tool()
def semantic_code_search_with_context(repo_path: str, query: str, top_k: int = 5):
    """
    Perform semantic search over a code repository using OpenAI embeddings.
    """
    repo = Repository(repo_path)
    repo.index(embed_fn=openai_embed)
    results = repo.search_semantic(query=query, top_k=top_k, embed_fn=openai_embed)
    return json.dumps(results)

### Initialize the server

if __name__ == "__main__":
    # Initialize and run the server
    mcp.run(transport='stdio')