"""
MiroFish Enterprise - MCP Server Package (app.mcp_server)
Re-exports canonical FastMCP server and tools for modular backend access.
"""
from mcp_server import *
from mcp_server.server import create_fastmcp_server, create_fastmcp_app, MCPServer
from mcp_server.tools import register_canonical_tools, register_mcp_tools

__all__ = [
    "create_fastmcp_server",
    "create_fastmcp_app",
    "MCPServer",
    "register_canonical_tools",
    "register_mcp_tools"
]
