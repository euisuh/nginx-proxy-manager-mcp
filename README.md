# npm-mcp

[![CI](https://github.com/euisuh/npm-mcp/actions/workflows/ci.yml/badge.svg)](https://github.com/euisuh/npm-mcp/actions/workflows/ci.yml)

An MCP (Model Context Protocol) server for [Nginx Proxy Manager](https://nginxproxymanager.com/). It lets an AI assistant such as Claude manage reverse-proxy hosts, Let's Encrypt certificates, and access lists through natural language instead of the NPM admin UI.

It runs as a Docker sidecar next to your existing NPM container, talks to the NPM REST API over the internal Docker network, and exposes 15 tools over MCP.

```
"Point blog.example.com at the container on port 3000 with HTTPS"
      │
      ▼
Claude ──MCP/SSE──► npm-mcp ──HTTP + JWT──► Nginx Proxy Manager API
```

## Architecture

```
┌─────────────┐   MCP over SSE    ┌──────────────────────────┐
│   Claude    │ ────────────────► │  npm-mcp  (FastMCP)      │
│  (client)   │  127.0.0.1:8000   │                          │
└─────────────┘                   │  server.py     bootstrap │
                                  │  npm_client.py auth/HTTP │
                                  │  tools/        15 tools  │
                                  └───────────┬──────────────┘
                                              │ HTTP + Bearer JWT
                                              ▼
                                  ┌──────────────────────────┐
                                  │  Nginx Proxy Manager     │
                                  │  app:81 (docker network) │
                                  └──────────────────────────┘
```

- **`server.py`** — validates required env vars, builds the FastMCP app, registers every tool module, and serves SSE. Docker uses SSE rather than stdio because a detached container has no stdin to read from.
- **`npm_client.py`** — a thin `httpx` wrapper. It exchanges the admin email/password for a JWT on first use, caches the token in memory, and transparently re-authenticates on a `401`. No token ever touches disk.
- **`tools/`** — one module per NPM resource. Each module exposes a `register_*_tools(mcp, client)` function, so adding a resource means adding one file and one registration line.

## Tools

| Category | Tools |
|---|---|
| Proxy hosts | `list_proxy_hosts`, `get_proxy_host`, `create_proxy_host`, `update_proxy_host`, `delete_proxy_host`, `enable_proxy_host`, `disable_proxy_host` |
| SSL certs | `list_certificates`, `create_letsencrypt_cert`, `renew_certificate` |
| Access lists | `list_access_lists`, `get_access_list`, `create_access_list`, `update_access_list`, `delete_access_list` |

## Quick start (Docker)

The bundled `docker-compose.yml` starts both Nginx Proxy Manager and npm-mcp. If you already run NPM, copy just the `npm-mcp` service into your existing compose file.

```bash
git clone https://github.com/euisuh/npm-mcp.git
cd npm-mcp
cp .env.example .env
# edit .env — NPM_EMAIL / NPM_PASSWORD must be an existing NPM admin account
docker compose up -d
```

`NPM_URL` defaults to `http://app:81`, the NPM admin API on the internal Docker network. Leave it as-is when both services share a compose stack; point it at your NPM host otherwise.

Then register the server with Claude Code:

```bash
claude mcp add npm http://localhost:8000/sse
```

Or add it manually to `~/.claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "npm": {
      "url": "http://localhost:8000/sse"
    }
  }
}
```

## Running locally (without Docker)

```bash
pip install -r mcp/requirements.txt
NPM_URL=http://localhost:81 \
NPM_EMAIL=admin@example.com \
NPM_PASSWORD=... \
python mcp/server.py
```

## Configuration

| Variable | Required | Default | Description |
| --- | --- | --- | --- |
| `NPM_URL` | yes | — | Base URL of the NPM admin API (`http://app:81` inside Docker) |
| `NPM_EMAIL` | yes | — | NPM admin account email |
| `NPM_PASSWORD` | yes | — | NPM admin account password |
| `MCP_HOST` | no | `0.0.0.0` | Bind address for the MCP server |
| `MCP_PORT` | no | `8000` | Bind port for the MCP server |

Missing required variables make the server exit with a clear error at startup rather than fail on the first API call.

## Project structure

```
mcp/
  server.py            # entrypoint: env validation, tool registration, SSE transport
  npm_client.py        # NPM REST client — JWT auth, retry on 401
  tools/
    proxy_hosts.py     # 7 proxy host tools
    ssl_certs.py       # 3 certificate tools
    access_lists.py    # 5 access list tools
  Dockerfile           # python:3.12-slim, runs as a non-root user
tests/                 # pytest + respx; NPM API is mocked, no live server needed
docker-compose.yml     # NPM + npm-mcp sidecar
```

## Development

```bash
pip install -r mcp/requirements.txt -r mcp/requirements-dev.txt
pytest -q
```

Tests mock the NPM API with [respx](https://lundberg.github.io/respx/), so the suite runs offline and touches no real infrastructure. CI runs the same command on every push and pull request.

## Security

- Credentials are supplied via environment variables only, never hardcoded, and `.env` is gitignored.
- The MCP port is published to `127.0.0.1` only — it is not reachable from the internet.
- The NPM admin JWT lives in process memory and is never written to disk.
- The container runs as a non-root user.
- Anything that can reach this MCP server has full admin control over your proxy hosts and certificates. Do not expose port 8000 publicly, and do not point it at an NPM instance you would not hand admin credentials for.

## Limitations

- Covers proxy hosts, certificates, and access lists only. Redirection hosts, streams, 404 hosts, users, audit log, and settings are not implemented.
- Certificate creation supports Let's Encrypt HTTP-01 only — no DNS-01 challenge, no custom certificate upload.
- One NPM instance per server process; there is no multi-tenant or multi-host routing.
- SSE transport only. stdio is not wired up, because the intended deployment is a detached Docker sidecar.
- No rate limiting and no per-tool authorization — the server trusts whatever MCP client connects to it.
- Written against the NPM v2 API; older or forked NPM builds may differ.

## Contributing

Issues and pull requests are welcome. Adding a new NPM resource follows a fixed shape:

1. Create `mcp/tools/<resource>.py` with a `register_<resource>_tools(mcp, client)` function.
2. Register it in `build_server()` in `mcp/server.py`.
3. Add `tests/test_<resource>.py` covering each tool with a respx-mocked NPM response.
4. Run `pytest -q` — CI runs the same suite.

Commits follow [Conventional Commits](https://www.conventionalcommits.org/).

## Author

Built and maintained by [Euisuh Jeong](https://github.com/euisuh) to manage a homelab reverse proxy from Claude Code.

## License

MIT — see [LICENSE](LICENSE).
