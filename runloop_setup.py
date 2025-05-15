from runloop_api_client import Runloop
import os
import sys

# Initialize Runloop client
runloop_client = Runloop(bearer_token=os.environ.get("RUNLOOP_API_KEY"))
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
GH_TOKEN = os.environ.get("GH_TOKEN")


def setup_devbox(name: str | None = None):
    dbx = runloop_client.devboxes.create_and_await_running(
        name=name or "runloop-example-code-understanding-with-mcp",
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
        metadata={"github_repo": "runloopai/runloop-example-code-understanding"},
    )
    print(f"Devbox created: {dbx.id}, proceeding to copy CLI files...")

    # Copy CLI files with error handling
    cli_files = {
        "kit_cli.py": "cli/kit_cli.py",
        "gh_cli.py": "cli/gh_cli.py",
        "traced_pytest_cli.py": "cli/traced_pytest_cli.py",
    }

    for target_path, source_path in cli_files.items():
        try:
            if not os.path.exists(source_path):
                print(f"Warning: {source_path} not found", file=sys.stderr)
                continue

            with open(source_path, "r") as f:
                contents = f.read()
                runloop_client.devboxes.write_file_contents(
                    dbx.id, file_path=f"/home/user/{target_path}", contents=contents
                )
        except Exception as e:
            print(f"Error copying {source_path}: {str(e)}", file=sys.stderr)

    print("CLI files copied to devbox, proceeding to test setup command...")

    runloop_client.devboxes.execute_sync(
        dbx.id,
        command="echo 'Setup complete! Moving to next step...'",
    )

    return dbx


def setup_devbox_with_dependencies():
    # Create new devbox with all necessary setup
    dbx = setup_devbox()

    # Create snapshot
    try:
        snapshot_description = (
            f"Initial setup for runloop-example-code-understanding-with-mcp"
        )
        snapshot_metadata = {
            "github_repo_link": "https://github.com/runloopai/runloop-example-code-understanding",
            "description": snapshot_description,
        }
        snapshot = runloop_client.devboxes.snapshot_disk(
            id=dbx.id,
            name="runloop-example-code-understanding-with-mcp",
            metadata=snapshot_metadata,
        )
        print(f"Successfully created snapshot: {snapshot.id}")
    except Exception as e:
        print(f"Error creating snapshot: {str(e)}", file=sys.stderr)
        return dbx, None

    runloop_client.devboxes.shutdown(dbx.id)

    return dbx, snapshot


def main():
    dbx, snapshot = setup_devbox_with_dependencies()

    if dbx:
        print(f"Setup complete! Devbox ID: {dbx.id}")
        print(f"Devbox name: {dbx.name}")
        print(f"Devbox status: {dbx.status}")

    if snapshot:
        print(f"Setup complete! Snapshot ID: {snapshot.id}")
        print(f"Snapshot name: {snapshot.name}")


if __name__ == "__main__":
    main()
