import pytest
import json
import tempfile
from runloop_mcp_config_setup import add_mcp_server_entry


@pytest.fixture
def temp_config_file():
    """Create a temporary config file with initial structure"""
    with tempfile.NamedTemporaryFile(mode="w+", delete=False) as f:
        initial_config = {
            "mcpServers": {
                "existing-server": {
                    "command": "existing-command",
                    "args": ["arg1"],
                    "env": {"KEY": "value"},
                }
            }
        }
        json.dump(initial_config, f)
        f.flush()
        return f.name


@pytest.fixture
def new_server_entry():
    """Sample new server entry for testing"""
    return {
        "command": "test-command",
        "args": ["--test", "arg"],
        "env": {"TEST_KEY": "test_value"},
    }


def test_add_new_server(temp_config_file, new_server_entry):
    server_name = "new-server"
    add_mcp_server_entry(temp_config_file, server_name, new_server_entry)
    with open(temp_config_file, "r") as f:
        config = json.load(f)
    assert server_name in config["mcpServers"]
    assert config["mcpServers"][server_name] == new_server_entry


def test_add_duplicate_server(temp_config_file, new_server_entry):
    server_name = "existing-server"
    with pytest.raises(Exception) as exc_info:
        add_mcp_server_entry(temp_config_file, server_name, new_server_entry)
    assert "already exists" in str(exc_info.value)


def test_add_server_preserves_existing(temp_config_file, new_server_entry):
    server_name = "new-server"
    with open(temp_config_file, "r") as f:
        initial_config = json.load(f)
    add_mcp_server_entry(temp_config_file, server_name, new_server_entry)
    with open(temp_config_file, "r") as f:
        updated_config = json.load(f)
    assert "existing-server" in updated_config["mcpServers"]
    assert (
        updated_config["mcpServers"]["existing-server"]
        == initial_config["mcpServers"]["existing-server"]
    )


def test_add_server_with_invalid_config(temp_config_file):
    with open(temp_config_file, "w") as f:
        f.write("invalid json")
    with pytest.raises(json.JSONDecodeError):
        add_mcp_server_entry(temp_config_file, "new-server", {})


def test_add_server_with_missing_mcpServers(new_server_entry):
    with tempfile.NamedTemporaryFile(mode="w+", delete=False) as f:
        json.dump({}, f)
        f.flush()
        temp_path = f.name
    # Should raise KeyError
    with pytest.raises(KeyError):
        add_mcp_server_entry(temp_path, "new-server", new_server_entry)


def test_add_server_with_empty_mcpServers(new_server_entry):
    with tempfile.NamedTemporaryFile(mode="w+", delete=False) as f:
        json.dump({"mcpServers": {}}, f)
        f.flush()
        temp_path = f.name
    add_mcp_server_entry(temp_path, "new-server", new_server_entry)
    with open(temp_path, "r") as f:
        config = json.load(f)
    assert "new-server" in config["mcpServers"]
    assert config["mcpServers"]["new-server"] == new_server_entry
