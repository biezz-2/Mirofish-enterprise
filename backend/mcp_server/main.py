"""
Titik Masuk Eksekusi FastMCP Server MiroFish Enterprise (Agent 17)
Mendukung Transport Streamable HTTP / SSE port 8080 (OAuth 2.1) dan Transport Stdio JSON-RPC 2.0.
"""

import sys
import os
import argparse
import logging

# Memastikan direktori backend berada di sys.path
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from mcp_server.server import MCPServer, create_fastmcp_app, DEFAULT_PORT, DEFAULT_HOST

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("mirofish.fastmcp_main")


def main():
    parser = argparse.ArgumentParser(description="MiroFish Enterprise Canonical FastMCP Server")
    parser.add_argument(
        "--transport",
        choices=["stdio", "http"],
        default=os.environ.get("MCP_TRANSPORT", "stdio"),
        help="Protokol transport server: 'http' (Streamable HTTP port 8080) atau 'stdio' (JSON-RPC)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=DEFAULT_PORT,
        help=f"Port listen FastMCP HTTP (default: {DEFAULT_PORT})"
    )
    parser.add_argument(
        "--host",
        type=str,
        default=DEFAULT_HOST,
        help=f"Host listen FastMCP HTTP (default: {DEFAULT_HOST})"
    )
    parser.add_argument(
        "--no-auth",
        action="store_true",
        help="Nonaktifkan proteksi OAuth 2.1 (hanya untuk mode dev lokal)"
    )

    args, unknown = parser.parse_known_args()

    if args.transport == "http" or "--http" in sys.argv:
        import uvicorn
        logger.info(f"Memulai MiroFish Canonical FastMCP Server [HTTP/SSE] pada {args.host}:{args.port} (OAuth 2.1 Active: {not args.no_auth})...")
        app = create_fastmcp_app(
            require_auth=not args.no_auth,
            port=args.port,
            host=args.host
        )
        uvicorn.run(app, host=args.host, port=args.port, log_level="info")
    else:
        logger.info("Memulai MiroFish Canonical FastMCP Server [stdio transport]...")
        server = MCPServer()
        server.run_stdio()


if __name__ == "__main__":
    main()
