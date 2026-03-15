import os
import re
import datetime
from google.adk.agents.llm_agent import Agent
from google.adk.tools.mcp_tool import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StdioConnectionParams, StreamableHTTPConnectionParams
from mcp import StdioServerParameters
from google.adk.tools import ToolContext
from google.adk.tools.base_tool import BaseTool
from typing import Dict, Any, Optional
from google.cloud import storage

get_weather = McpToolset(
    connection_params=StreamableHTTPConnectionParams(
        url="your-weather-mcp-cloud-run-url/mcp", # TODO: Add your Weather MCP URL
        timeout=60,
    )
)

google_maps_api_key = os.environ.get("GOOGLE_MAPS_API_KEY")
if not google_maps_api_key:
    raise ValueError("GOOGLE_MAPS_API_KEY environment variable is not set")
headers = {
    "X-Goog-Api-Key": google_maps_api_key,
}
get_coordinates = McpToolset(
    connection_params=StreamableHTTPConnectionParams(
        url="https://mapstools.googleapis.com/mcp",
        headers=headers,
        timeout=10,
    ), tool_filter=["search_places"]
)

cloud_storage_url = "gs://your-genmedia-mcp-bucket" # TODO: Add your bucket gs link
generate_weather_postcard = McpToolset(
    connection_params=StreamableHTTPConnectionParams(
        url="your-genmedia-imagen-go-mcp-server-cloud-run-url/mcp", # TODO: Add your Imagen MCP url
        timeout=60,
        
    ), tool_filter=["imagen_t2i"]
)

agentmail_env = os.environ.copy()
agentmail_env["AGENTMAIL_API_KEY"] = os.environ.get("AGENTMAIL_API_KEY")
inbox_id="your-inbox-id" # TODO: Add your Inbox ID from AgentMail
send_email = McpToolset(
    connection_params=StdioConnectionParams(
        server_params=StdioServerParameters(
            command="npx",
            args=[
                "-y",
                "agentmail-mcp",
            ],
            env=agentmail_env
        ),
        timeout=10,
    ), tool_filter=["send_message"]
)

root_agent = Agent(
    model='gemini-2.5-flash',
    name='root_agent',
    description='A helpful assistant for giving weather updates of a US location, creating weather postcards and sending the weather summary and postcard on email.',
    instruction=f"""
        You are helpful assistant that tells the weather of a US location using 'get_weather' tool.
        When the user provides a location, use 'get_coordinates' to get the latitude and longitude of the place.
        And pass the latitude and longitude with 2 decimal points to the 'get_weather' tool to provide weather details.
        When user asks to generate the postcard, use the 'generate_weather_postcard' tool.
        You will generate a postcard image of aspect_ratio of 16:9 for the weather summary in the place specified by the user.
        The image should be animated and colorful.
        Store the generated postcard image to google cloud storage: {cloud_storage_url}.
        You can return the HTTPS URL to the user!
        When prompted to email the weather postcard, use 'send_email' tool to send the email.
        Create an nice HTML body that includes the weather summary in poetic form and the hyperlinked image URL to the postcard.
        Subject should always be 'Weather Summary'.
        Note: We are not sending any attachments.
        You can use {inbox_id} as the inbox_id for sending the email.
    """,
    tools=[get_coordinates, get_weather, generate_weather_postcard, send_email]
)
