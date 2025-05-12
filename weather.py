from typing import Any
import httpx
from mcp.server.fastmcp import FastMCP
import os
from runloop_api_client import Runloop
import json

# Initialize FastMCP server
mcp = FastMCP("code-understanding")

runloop_client = Runloop(bearer_token=os.environ.get("RUNLOOP_API_KEY"))

running_devboxes: dict[str, str] = {}

oaikey = "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"

generate_repo_map_cmd = f"cd /home/user/runloop-examples && wget -qO- https://aider.chat/install.sh | sh && touch ./generated_repo_map.txt && aider --model o3-mini --api-key openai=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 --yes-always --show-repo-map > ./generated_repo_map.txt"

# Public devbox
async def launch_devbox_with_code_mount(github_repo_link: str):
    if github_repo_link in running_devboxes:
        return running_devboxes[github_repo_link]
    else:
        dbx = runloop_client.devboxes.create_and_await_running(
            code_mounts=[
            {
            "repo_name": github_repo_link.split("/")[-1],
            "repo_owner": github_repo_link.split("/")[-2],
            }
        ]
        )
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

if __name__ == "__main__":
    # Initialize and run the server
    mcp.run(transport='stdio')


'''
# Constants
NWS_API_BASE = "https://api.weather.gov"
USER_AGENT = "weather-app/1.0"

async def make_nws_request(url: str) -> dict[str, Any] | None:
    """Make a request to the NWS API with proper error handling."""
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "application/geo+json"
    }
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers, timeout=30.0)
            response.raise_for_status()
            return response.json()
        except Exception:
            return None

def format_alert(feature: dict) -> str:
    """Format an alert feature into a readable string."""
    props = feature["properties"]
    return f"""
Event: {props.get('event', 'Unknown')}
Area: {props.get('areaDesc', 'Unknown')}
Severity: {props.get('severity', 'Unknown')}
Description: {props.get('description', 'No description available')}
Instructions: {props.get('instruction', 'No specific instructions provided')}
"""

@mcp.tool()
async def get_alerts(state: str) -> str:
    """Get weather alerts for a US state.

    Args:
        state: Two-letter US state code (e.g. CA, NY)
    """
    url = f"{NWS_API_BASE}/alerts/active/area/{state}"
    data = await make_nws_request(url)

    if not data or "features" not in data:
        return "Unable to fetch alerts or no alerts found."

    if not data["features"]:
        return "No active alerts for this state."

    alerts = [format_alert(feature) for feature in data["features"]]
    return "\n---\n".join(alerts)

@mcp.tool()
async def get_forecast(latitude: float, longitude: float) -> str:
    """Get weather forecast for a location.

    Args:
        latitude: Latitude of the location
        longitude: Longitude of the location
    """
    # First get the forecast grid endpoint
    points_url = f"{NWS_API_BASE}/points/{latitude},{longitude}"
    points_data = await make_nws_request(points_url)

    if not points_data:
        return "Unable to fetch forecast data for this location."

    # Get the forecast URL from the points response
    forecast_url = points_data["properties"]["forecast"]
    forecast_data = await make_nws_request(forecast_url)

    if not forecast_data:
        return "Unable to fetch detailed forecast."

    # Format the periods into a readable forecast
    periods = forecast_data["properties"]["periods"]
    forecasts = []
    for period in periods[:5]:  # Only show next 5 periods
        forecast = f"""
{period['name']}:
Temperature: {period['temperature']}°{period['temperatureUnit']}
Wind: {period['windSpeed']} {period['windDirection']}
Forecast: {period['detailedForecast']}
"""
        forecasts.append(forecast)

    return "\n---\n".join(forecasts)
    '''