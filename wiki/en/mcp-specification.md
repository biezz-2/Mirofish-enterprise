# Model Context Protocol (MCP) Server Specification

## 1. Overview & Architectural Context

MiroFish Enterprise implements a standardized **Model Context Protocol (MCP)** server (`backend/mcp_server/`) compliant with the MCP specification (2024-11-05). The server exposes MiroFish's multi-agent social simulation engine, GraphRAG knowledge graph, SearXNG web research grounding, and executive report generation capabilities to external AI clients, coding assistants, and orchestration swarms.

---

## 2. Transport Architecture & Decision

MiroFish MCP adopts a **Dual-Transport Architecture** tailored to local developer workflows and remote containerized production environments:

| Feature / Criteria | `stdio` Transport | `streamable-http` Transport |
| :--- | :--- | :--- |
| **Primary Target** | Local CLI Integration (Claude Code, Cursor IDE, local LLM runners) | Remote / Containerized Deployment (Docker Compose, Kubernetes, Swarm) |
| **Default Port** | N/A (Standard I/O stream) | Port `8091` (Configurable via `MCP_SERVER_PORT` / `--port`) |
| **Protocol** | JSON-RPC 2.0 over `stdin` / `stdout` (line-delimited JSON) | Streamable HTTP / SSE (Starlette + Uvicorn ASGI) |
| **Authentication** | Process boundary / OS file permissions (implicit) | OAuth 2.1 (RFC 7636 PKCE S256 & RFC 7662 Introspection) or `--no-auth` |
| **Network Exposure** | None (zero attack surface) | `127.0.0.1:8091` (loopback / ingress bridge) |
| **Healthcheck** | Process lifecycle / exit code | HTTP GET `/health` returning JSON status |

### 2.1 Decision Rationale

1. **`stdio` for Local CLI Integration**:
   - Claude Code, Claude Desktop, and Cursor IDE spawn MCP servers as child processes communicating over pipes (`stdin`/`stdout`).
   - Eliminates port conflicts, binding errors, firewall interference, and token handshake overhead on developer workstations.
   - Command: `python3 mcp_server/main.py --transport stdio`

2. **`streamable-http` for Remote & Containerized Deployment**:
   - In distributed deployments (`docker-compose.yml`), external agent services and monitoring agents require a network addressable endpoint.
   - Listens on port `8091` to avoid collisions with MiroFish Core API (`8000`), SearXNG (`8080`/`8888`), Graphiti (`8090`), and Neo4j (`7474`/`7687`).
   - Supports HTTP Streaming / Server-Sent Events (SSE) for long-running simulation streaming.
   - Command: `python3 mcp_server/main.py --transport http --port 8091 --no-auth`

---

## 3. Endpoints & Health Contract

### 3.1 Health Check Endpoint (`/health`)

The HTTP transport exposes `GET /health` with the standardized status contract:

```json
{
  "status": "healthy",
  "service": "mirofish-mcp-server",
  "transport": "streamable-http",
  "fastmcp_port": 8091,
  "oauth_required": false,
  "backends": {
    "fastmcp_streamable_http": "RUNNING (port 8080)",
    "oauth_2_1_auth_server": "ENABLED (RFC 7636 PKCE S256 & RFC 7662)",
    "searxng_service": "CONNECTED (port 8888)",
    "graphiti_service": "CONNECTED (port 8090)",
    "redis_state_cache": "CONNECTED (6379)",
    "vault_aes256_gcm": "VERIFIED_ENCRYPTED (~/.hermes/mirofish_vault.enc)"
  },
  "active_tools_count": 11,
  "integrity_check": "PASSED"
}
```

This endpoint is verified by the container `HEALTHCHECK` directive and automated CI test suites.

### 3.2 Metadata & OAuth 2.1 Endpoints

- `GET /tools`: Lists all registered canonical MCP tools and parameter schemas.
- `GET /.well-known/oauth-authorization-server`: RFC 8414 OAuth 2.0 authorization server metadata.
- `GET/POST /oauth/authorize`: OAuth 2.1 authorization endpoint with PKCE verification.
- `POST /oauth/token`: Token exchange endpoint (RFC 6749 / RFC 7636).
- `POST /oauth/introspect`: Token introspection endpoint (RFC 7662).

---

## 4. Containerization & Docker Compose

### 4.1 Dockerfile (`backend/Dockerfile.mcp`)

- **Base Image**: `python:3.12-slim`
- **Security**: Runs under non-root user `mirofish` (uid: 1000, gid: 1000).
- **Dependencies**: Built via multi-stage build caching `requirements.txt` / `pyproject.toml`.
- **Exposed Port**: `8091`
- **Healthcheck**:
  ```dockerfile
  HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
      CMD python3 -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8091/health')"
  ```
- **Entrypoint**:
  ```dockerfile
  CMD ["python3", "mcp_server/main.py", "--transport", "http", "--port", "8091", "--no-auth"]
  ```

### 4.2 Docker Compose Service (`docker-compose.yml`)

```yaml
  mcp-server:
    build:
      context: ./backend
      dockerfile: Dockerfile.mcp
    container_name: mirofish-mcp-server
    restart: unless-stopped
    ports:
      - "127.0.0.1:8091:8091"
    environment:
      - MCP_SERVER_PORT=8091
      - MCP_SERVER_HOST=0.0.0.0
      - BACKEND_API_URL=http://backend:8000
    healthcheck:
      test: ["CMD", "python3", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8091/health')"]
      interval: 30s
      timeout: 5s
      start_period: 10s
      retries: 3
    depends_on:
      backend:
        condition: service_healthy
```

---

## 5. Canonical MCP Tools Catalog

The MCP server registers 11 canonical tools plus downstream analytics:

1. `create_simulation_project`: Initialize predictive simulation workspace.
2. `trigger_web_research`: Execute SearXNG grounded search with anti-injection shield.
3. `build_knowledge_graph`: Construct entity-relation graph in Neo4j/Graphiti.
4. `generate_agent_profiles`: Generate synthetic persona agents (OCEAN / Demographics).
5. `calibrate_platform_algorithms`: Calibrate feed dynamics across 7 social platforms.
6. `execute_parallel_simulation`: Run parallel multi-agent simulation rounds.
7. `fetch_simulation_stream`: Stream real-time events and agent actions via SSE.
8. `query_graph_insights`: Query ontology subgraphs and temporal community shifts.
9. `generate_executive_report`: Compile C-Level executive strategic report with SHA-256 integrity.
10. `interview_simulation_agent`: Real-time ReACT dialogue with simulated agent personas.
11. `audit_system_diagnostics`: Comprehensive system integrity and backend service audit.
