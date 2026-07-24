# Nginx Proxy Manager MCP

[![CI](https://github.com/euisuh/nginx-proxy-manager-mcp/actions/workflows/ci.yml/badge.svg)](https://github.com/euisuh/nginx-proxy-manager-mcp/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

An MCP server for [Nginx Proxy Manager](https://nginxproxymanager.com/). It lets Claude and other MCP clients manage reverse-proxy hosts, Let's Encrypt certificates, and access lists through typed tools instead of clicking through the NPM admin UI.

```text
"Point blog.example.com at the container on port 3000 with HTTPS"
      │
      ▼
Claude / MCP client ──► Nginx Proxy Manager MCP ──HTTP + JWT──► NPM API
```

## Why this exists

Reverse-proxy changes are repetitive homelab work: create a host, point it at a container, attach a certificate, maybe restrict it to an access list. That is exactly the kind of operational task an AI assistant can handle well when it has narrow, typed tools and a local admin boundary.

This server runs either:

- as an SSE Docker sidecar next to an existing NPM container, or
- as a stdio MCP server for local clients.

## Features

- 16 MCP tools for common NPM operations.
- `dry_run` previews for mutating tools, so an MCP client can show the exact NPM request before applying it.
- JWT auth against the NPM API with in-memory token caching and automatic re-authentication on `401`.
- Docker sidecar deployment that binds the MCP port to localhost by default.
- Offline pytest suite with mocked NPM API responses.
- No token persistence and no hardcoded credentials.

## Tools

| Category | Tools |
|---|---|
| Workflows | `create_proxy_host_with_letsencrypt` |
| Proxy hosts | `list_proxy_hosts`, `get_proxy_host`, `create_proxy_host`, `update_proxy_host`, `delete_proxy_host`, `enable_proxy_host`, `disable_proxy_host` |
| SSL certs | `list_certificates`, `create_letsencrypt_cert`, `renew_certificate` |
| Access lists | `list_access_lists`, `get_access_list`, `create_access_list`, `update_access_list`, `delete_access_list` |

Every create, update, delete, enable, disable, certificate request, and certificate renewal tool accepts `dry_run=True` to return a structured `{method, path, json}` preview without sending the mutating request to NPM.

## Quick start: Docker sidecar

The bundled `docker-compose.yml` starts both Nginx Proxy Manager and this MCP sidecar from source. If you already run NPM, copy only the `nginx-proxy-manager-mcp` service into your existing compose file.

```bash
git clone https://github.com/euisuh/nginx-proxy-manager-mcp.git
cd nginx-proxy-manager-mcp
cp .env.example .env
# edit .env — NPM_EMAIL / NPM_PASSWORD must be an existing NPM admin account
docker compose up -d
```

`NPM_URL` defaults to `http://app:81`, the NPM admin API on the internal Docker network. Leave it as-is when both services share a compose stack; point it at your NPM host otherwise.

To use the published GHCR image instead of building locally:

```yaml
services:
  nginx-proxy-manager-mcp:
    image: ghcr.io/euisuh/nginx-proxy-manager-mcp:latest
    restart: unless-stopped
    environment:
      NPM_URL: http://app:81
      NPM_EMAIL: ${NPM_EMAIL}
      NPM_PASSWORD: ${NPM_PASSWORD}
      MCP_TRANSPORT: sse
      MCP_HOST: 0.0.0.0
      MCP_PORT: 8000
    ports:
      - "127.0.0.1:8000:8000"
```

Register the SSE server with Claude Code:

```bash
claude mcp add npm http://localhost:8000/sse
```

Or add it manually to an MCP client config:

```json
{
  "mcpServers": {
    "nginx-proxy-manager": {
      "url": "http://localhost:8000/sse"
    }
  }
}
```

## Quick start: stdio

Use stdio when you want the MCP client to launch the server process directly instead of talking to a sidecar.

```bash
python -m venv .venv
. .venv/bin/activate
pip install -r mcp/requirements.txt
NPM_URL=http://localhost:81 \
NPM_EMAIL=admin@example.com \
NPM_PASSWORD=... \
MCP_TRANSPORT=stdio \
python mcp/server.py
```

Example client config:

```json
{
  "mcpServers": {
    "nginx-proxy-manager": {
      "command": "/path/to/nginx-proxy-manager-mcp/.venv/bin/python",
      "args": ["/path/to/nginx-proxy-manager-mcp/mcp/server.py"],
      "env": {
        "NPM_URL": "http://localhost:81",
        "NPM_EMAIL": "admin@example.com",
        "NPM_PASSWORD": "...",
        "MCP_TRANSPORT": "stdio"
      }
    }
  }
}
```

## Configuration

| Variable | Required | Default | Description |
|---|---:|---|---|
| `NPM_URL` | yes | — | Base URL of the NPM admin API (`http://app:81` inside Docker) |
| `NPM_EMAIL` | yes | — | NPM admin account email |
| `NPM_PASSWORD` | yes | — | NPM admin account password |
| `MCP_TRANSPORT` | no | `sse` | MCP transport: `sse` or `stdio` |
| `MCP_HOST` | no | `0.0.0.0` | Bind address for SSE mode |
| `MCP_PORT` | no | `8000` | Bind port for SSE mode |

Missing required variables make the server exit with a clear error at startup rather than fail on the first API call.

## Architecture

```text
┌───────────────┐   MCP over SSE/stdio   ┌──────────────────────────┐
│ Claude/Cursor │ ─────────────────────► │ Nginx Proxy Manager MCP  │
│ / MCP client  │                        │ server.py + tools/       │
└───────────────┘                         └───────────┬──────────────┘
                                                       │ HTTP + Bearer JWT
                                                       ▼
                                           ┌──────────────────────────┐
                                           │ Nginx Proxy Manager API  │
                                           │ app:81 / localhost:81    │
                                           └──────────────────────────┘
```

- `mcp/server.py` validates required env vars, builds the FastMCP app, registers every tool module, and serves either SSE or stdio.
- `mcp/npm_client.py` wraps `httpx`, exchanges the admin email/password for a JWT on first use, caches the token in memory, and re-authenticates on `401`.
- `mcp/tools/` keeps one module per NPM resource. Adding a resource means adding one `register_*_tools(mcp, client)` function and one registration line.

## Development

```bash
python -m venv .venv
. .venv/bin/activate
pip install -r mcp/requirements.txt -r mcp/requirements-dev.txt
pytest -q
```

Tests mock the NPM API with [respx](https://lundberg.github.io/respx/), so the suite runs offline and touches no real infrastructure. CI runs the same command on every push and pull request.

## Releases

Tagged releases publish multi-architecture Docker images to GitHub Container Registry:

- `ghcr.io/euisuh/nginx-proxy-manager-mcp:<version>` for tags such as `v0.2.0`
- `ghcr.io/euisuh/nginx-proxy-manager-mcp:<major>.<minor>` for semver tags
- `ghcr.io/euisuh/nginx-proxy-manager-mcp:latest` for the newest tagged release

The Docker workflow also builds pull requests without pushing an image, so packaging changes are validated before release.

## Security

Anything that can reach this MCP server has admin-level control over your proxy hosts and certificates.

- Do not expose the MCP endpoint publicly.
- Keep the Docker port bound to `127.0.0.1` unless you have another trusted network boundary.
- Use environment variables or a secrets manager for NPM credentials; do not commit `.env`.
- The NPM admin JWT lives in process memory and is never written to disk.
- The container runs as a non-root user.

See [SECURITY.md](SECURITY.md) for reporting and deployment guidance.

## Roadmap

See [ROADMAP.md](ROADMAP.md). Near-term priorities are safer mutating tools, a one-shot “create host with certificate” workflow, broader NPM resource coverage, and packaged container releases.

## Limitations

- Covers proxy hosts, certificates, and access lists only. Redirection hosts, streams, 404 hosts, users, audit log, and settings are not implemented yet.
- Certificate creation supports Let's Encrypt HTTP-01 only — no DNS-01 challenge and no custom certificate upload yet.
- One NPM instance per server process; there is no multi-tenant or multi-host routing.
- No built-in per-tool authorization. The server trusts whatever MCP client connects to it.
- Written against the NPM v2 API; older or forked NPM builds may differ.

## Contributing

Issues and pull requests are welcome. Adding a new NPM resource follows a fixed shape:

1. Create `mcp/tools/<resource>.py` with a `register_<resource>_tools(mcp, client)` function.
2. Register it in `build_server()` in `mcp/server.py`.
3. Add `tests/test_<resource>.py` covering each tool with respx-mocked NPM responses.
4. Run `pytest -q`.

Commits follow [Conventional Commits](https://www.conventionalcommits.org/).

## Author

Built and maintained by [Euisuh Jeong](https://github.com/euisuh) to manage a homelab reverse proxy from Claude Code.

## License

MIT — see [LICENSE](LICENSE).
