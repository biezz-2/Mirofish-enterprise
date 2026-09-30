"""
Titik Masuk Eksekusi Server MCP MiroFish
"""
from mcp_server.server import MCPServer

if __name__ == "__main__":
    server = MCPServer()
    server.run_stdio()
