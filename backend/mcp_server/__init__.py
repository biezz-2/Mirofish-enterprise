"""
Model Context Protocol (MCP) Server untuk MiroFish
Mengekspos alat-alat operasional simulasi berbasis AI-native (stdio & Streamable HTTP)
"""
from .tools import register_mcp_tools

__all__ = ["register_mcp_tools"]
