from runloop_api_client import Runloop
import os
import sys

# Try to import rich for colored output, fallback to print if not available
try:
    from rich import print as rprint
    from rich.console import Console

    console = Console()

    def info(msg):
        rprint(f":rocket: [bold cyan]{msg}[/bold cyan]")

    def success(msg):
        rprint(f":sparkles: [bold green]{msg}[/bold green]")

    def warn(msg):
        rprint(f":warning: [bold yellow]{msg}[/bold yellow]")

    def error(msg):
        rprint(f":x: [bold red]{msg}[/bold red]")

except ImportError:

    def info(msg):
        print(f"[INFO] {msg}")

    def success(msg):
        print(f"[SUCCESS] {msg}")

    def warn(msg):
        print(f"[WARN] {msg}")

    def error(msg):
        print(f"[ERROR] {msg}")


# Initialize Runloop client
runloop_client = Runloop(bearer_token=os.environ.get("RUNLOOP_API_KEY"))
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
GH_TOKEN = os.environ.get("GH_TOKEN")


def setup_devbox(name: str | None = None):
    info(f"Creating devbox: {name or 'demo-code-understanding-mcp'} ...")
    # Create a new devbox and wait for it to be running (DevboxesResource.create_and_await_running)
    dbx = runloop_client.devboxes.create_and_await_running(
        name=name or "demo-code-understanding-mcp",
        launch_parameters={
            "launch_commands": [
                "sudo apt-get update",
                "sudo apt-get install -y libsqlite3-dev",
                "echo 'Installing pip dependencies'",
                "pip install --user cased-kit openai chromadb pytest",
                "echo 'Installing aider'",
                "wget -qO- https://aider.chat/install.sh | sh",
                "echo 'Setting up environment variables'",
                "echo 'export PATH=$PATH:~/.local/bin' >> ~/.bashrc",  # Add to .bashrc
                "source ~/.bashrc",  # Reload the profile
            ]
        },
        environment_variables={
            "OPENAI_API_KEY": os.environ.get("OPENAI_API_KEY"),
            "GH_TOKEN": os.environ.get("GH_TOKEN"),
        },
        metadata={"github_repo": "runloopai/demo-code-understanding-mcp"},
    )
    success(f"Devbox created: {dbx.id}")
    info("Copying CLI files to devbox ...")

    # Copy CLI files with error handling
    cli_files = {
        "kit_cli.py": "cli/kit_cli.py",
        "gh_cli.py": "cli/gh_cli.py",
        "traced_pytest_cli.py": "cli/traced_pytest_cli.py",
    }

    for target_path, source_path in cli_files.items():
        try:
            if not os.path.exists(source_path):
                warn(f"{source_path} not found, skipping.")
                continue

            with open(source_path, "r") as f:
                contents = f.read()
                # Write file contents to the devbox (DevboxesResource.write_file_contents)
                runloop_client.devboxes.write_file_contents(
                    dbx.id, file_path=f"/home/user/{target_path}", contents=contents
                )
            success(f"Copied {source_path} to devbox as {target_path}")
        except Exception as e:
            error(f"Error copying {source_path}: {str(e)}")

    info("Testing devbox setup ...")
    # Execute a shell command synchronously in the devbox (DevboxesResource.execute_sync)
    runloop_client.devboxes.execute_sync(
        dbx.id,
        command="echo 'Setup complete! Moving to next step...'",
    )
    success("CLI files copied and setup command executed.")

    return dbx


def setup_devbox_with_dependencies():
    info("Setting up devbox with dependencies and creating snapshot ...")
    dbx = setup_devbox()

    # Create snapshot
    try:
        snapshot_description = f"Initial setup for demo-code-understanding-mcp"
        snapshot_metadata = {
            "github_repo_link": "https://github.com/runloopai/demo-code-understanding-mcp",
            "description": snapshot_description,
        }
        # Create a disk snapshot of the devbox (DevboxesResource.snapshot_disk)
        snapshot = runloop_client.devboxes.snapshot_disk(
            id=dbx.id,
            name="demo-code-understanding-mcp",
            metadata=snapshot_metadata,
            timeout=600,
        )
        success(f"Snapshot created: {snapshot.id}")
    except Exception as e:
        error(f"Error creating snapshot: {str(e)}")
        return dbx, None

    info("Shutting down devbox ...")
    # Shutdown the devbox (DevboxesResource.shutdown)
    runloop_client.devboxes.shutdown(dbx.id)
    success("Devbox shutdown complete.")

    return dbx, snapshot


def main():
    info(":hammer_and_wrench: Starting devbox and snapshot setup ...")
    dbx, snapshot = setup_devbox_with_dependencies()

    if dbx:
        success(f"Setup complete! Devbox ID: {dbx.id}")
        info(f"Devbox name: {dbx.name}")
        info(f"Devbox status: {dbx.status}")

    if snapshot:
        success(f"Snapshot complete! Snapshot ID: {snapshot.id}")
        info(f"Snapshot name: {snapshot.name}")
    else:
        warn("No snapshot was created.")

    success(":tada: All done!")


if __name__ == "__main__":
    main()
