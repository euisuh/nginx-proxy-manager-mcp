# Nginx Proxy Manager MCP

<!-- mcp-name: io.github.euisuh/nginx-proxy-manager-mcp -->

[![CI](https://github.com/euisuh/nginx-proxy-manager-mcp/actions/workflows/ci.yml/badge.svg)](https://github.com/euisuh/nginx-proxy-manager-mcp/actions/workflows/ci.yml)
[![Docker](https://github.com/euisuh/nginx-proxy-manager-mcp/actions/workflows/docker.yml/badge.svg)](https://github.com/euisuh/nginx-proxy-manager-mcp/actions/workflows/docker.yml)
[![Python Package](https://github.com/euisuh/nginx-proxy-manager-mcp/actions/workflows/python-package.yml/badge.svg)](https://github.com/euisuh/nginx-proxy-manager-mcp/actions/workflows/python-package.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

An MCP server for [Nginx Proxy Manager](https://nginxproxymanager.com/). It lets Claude and other MCP clients manage reverse-proxy hosts, Let's Encrypt certificates, and access lists through typed tools instead of clicking through the NPM admin UI.

```text
"Point blog.example.com at the container on port 3000 with HTTPS"
      │
      ▼
Claude / MCP client ──► Nginx Proxy Manager MCP ──HTTP + JWT──► NPM API
```

![Dry-run preview of creating an HTTPS proxy host](docs/demo.gif)

The demo calls `create_proxy_host_with_letsencrypt(dry_run=True)` against a mocked NPM API and prints both request previews. No real NPM instance or credentials are used. To record it again, install the development dependencies and VHS, then run `vhs docs/demo.tape` from the repository root; [`docs/demo.py`](docs/demo.py) uses the same respx mocking approach as the tests.

## Why this exists

Reverse-proxy changes are repetitive homelab work: create a host, point it at a container, attach a certificate, maybe restrict it to an access list. That is exactly the kind of operational task an AI assistant can handle well when it has narrow, typed tools and a local admin boundary.

This server runs either:

- as an SSE Docker sidecar next to an existing NPM container, or
- as a stdio MCP server for local clients.

## Features

- 30 MCP tools for common NPM operations.
- `dry_run` on all mutating tools to preview NPM requests before applying them;
- One-shot `create_proxy_host_with_letsencrypt` requests a certificate, then creates an HTTPS-forced proxy host.
- JWT auth against the NPM API with in-memory token caching and automatic re-authentication on `401`.
- Docker sidecar deployment that binds the MCP port to localhost by default.
- Offline pytest suite with mocked NPM API responses.
- Ruff quality gate and contributor templates for public maintenance.
- Python wheel build validation and MCP directory metadata for promotion readiness.
- No token persistence and no hardcoded credentials.

## Tools

| Category | Tools |
|---|---|
| Workflows | `create_proxy_host_with_letsencrypt` |
| Proxy hosts | `list_proxy_hosts`, `get_proxy_host`, `create_proxy_host`, `update_proxy_host`, `delete_proxy_host`, `enable_proxy_host`, `disable_proxy_host` |
| Redirection hosts | `list_redirection_hosts`, `get_redirection_host`, `create_redirection_host`, `update_redirection_host`, `delete_redirection_host`, `enable_redirection_host`, `disable_redirection_host` |
| Streams | `list_streams`, `get_stream`, `create_stream`, `update_stream`, `delete_stream`, `enable_stream`, `disable_stream` |
| SSL certs | `list_certificates`, `create_letsencrypt_cert`, `renew_certificate` |
| Access lists | `list_access_lists`, `get_access_list`, `create_access_list`, `update_access_list`, `delete_access_list` |

List tools support optional server-side filtering after fetching from NPM: `domain` matches a case-insensitive substring in any domain name for proxy hosts, redirection hosts, and certificates; `enabled` filters proxy hosts, redirection hosts, and streams by status. All four accept `compact=True` to return only summary fields. Filters combine, and calls without arguments return the full, unchanged NPM list. For example, `list_proxy_hosts(domain="example", enabled=True, compact=True)` lists enabled hosts matching "example" with compact output.

All mutating tools expose `dry_run=True`. Previews contain `method` and `path`, plus `json` when the request has a body; the HTTPS workflow returns two previews in `steps`. The flag suppresses mutating requests, though some previews read current state. Update tools send only the fields in NPM's PUT schema (fixes [#19](https://github.com/euisuh/nginx-proxy-manager-mcp/issues/19)); this is covered by mocked tests and not yet checked against a live NPM instance.

## Compared to other NPM MCP servers

Competitor facts below come only from their linked READMEs fetched with `gh api repos/<owner>/nginx-proxy-manager-mcp/readme` on 2026-10-13. “not documented” means the README does not establish the capability, not that it is absent. Auth guard means inbound MCP client authentication, distinct from NPM API login.

| Repository | Tool count documented | Dry-run support | Transport | Auth guard |
|---|---:|---|---|---|
| [euisuh (this server)](https://github.com/euisuh/nginx-proxy-manager-mcp) | 30 | `dry_run` on all mutating tools | stdio, SSE | Optional SSE bearer token (`MCP_BEARER_TOKEN`); `/healthz` exempt |
| [b3nw](https://github.com/b3nw/nginx-proxy-manager-mcp/blob/725d323b96c5d4e88790b8c88ea790a1133fc2d1/README.md) | 14 named tools (13 catalog rows plus `list_instances`) | not documented | stdio, HTTP | HTTP bearer token (`NPM_MCP_AUTH_TOKEN`) |
| [omichelbraga](https://github.com/omichelbraga/nginx-proxy-manager-mcp/blob/c6568f0f090c8a087ac9f3a56ac468c139e0a3cb/README.md) | 66 | DELETE without `confirm: true` previews affected resources; general `dry_run` not documented | stdio, Streamable HTTP | Optional bearer token (`NPM_MCP_BEARER_TOKEN`); unset means no inbound auth |
| [drmogie](https://github.com/drmogie/nginx-proxy-manager-mcp/blob/91c4176b544de6b64b9d16ff6dc891a352951145/README.md) | 4 named tools (`npm_status`, `npm_hosts`, `npm_audit_log`, `npm_call`) | Changes show what will be sent and require `confirm`; `dry_run` not documented | not documented | not documented |

This server's implementations expose `dry_run` on every mutating tool, provide the one-shot `create_proxy_host_with_letsencrypt` workflow, and publish the Docker sidecar at `127.0.0.1:8000:8000`. These are verified in [`tools/`](nginx_proxy_manager_mcp/tools/), [`server.py`](nginx_proxy_manager_mcp/server.py), and [`docker-compose.yml`](docker-compose.yml). They do not establish that other servers lack equivalent capabilities.

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
      MCP_BEARER_TOKEN: ${MCP_BEARER_TOKEN:-}
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

More examples live in [`examples/`](examples/): Claude Desktop, Claude Code, Cursor, and Windsurf.

## Quick start: uvx / pipx

If you do not want Docker, run it from PyPI (package `nginx-proxy-manager-mcp-server`):

```bash
NPM_URL=http://localhost:81 \
NPM_EMAIL=admin@example.com \
NPM_PASSWORD=... \
MCP_TRANSPORT=stdio \
uvx nginx-proxy-manager-mcp-server
```

Or from a local checkout:

```bash
git clone https://github.com/euisuh/nginx-proxy-manager-mcp.git
cd nginx-proxy-manager-mcp

NPM_URL=http://localhost:81 \
NPM_EMAIL=admin@example.com \
NPM_PASSWORD=... \
MCP_TRANSPORT=stdio \
uvx --from . nginx-proxy-manager-mcp
```

Or install it into an isolated environment:

```bash
pipx install nginx-proxy-manager-mcp-server
```

## Quick start: stdio

Use stdio when you want the MCP client to launch the server process directly instead of talking to a sidecar.

```bash
python -m venv .venv
. .venv/bin/activate
pip install -e .
NPM_URL=http://localhost:81 \
NPM_EMAIL=admin@example.com \
NPM_PASSWORD=... \
MCP_TRANSPORT=stdio \
nginx-proxy-manager-mcp
```

Example client config:

```json
{
  "mcpServers": {
    "nginx-proxy-manager": {
      "command": "/path/to/nginx-proxy-manager-mcp/.venv/bin/python",
      "args": ["-m", "nginx_proxy_manager_mcp.server"],
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
| `NPM_READ_ONLY` | no | disabled | `1`, `true`, or `yes` (case-insensitive) registers only `list_`, `get_`, and `find_` tools; all other values disable read-only mode |
| `MCP_TRANSPORT` | no | `sse` | MCP transport: `sse` or `stdio` |
| `MCP_HOST` | no | `127.0.0.1` | Bind address for SSE mode; Docker Compose sets `0.0.0.0` inside the container while publishing only to localhost |
| `MCP_PORT` | no | `8000` | Bind port for SSE mode |
| `MCP_BEARER_TOKEN` | no | — | Optional bearer token required for SSE HTTP requests |

Set `NPM_READ_ONLY=true` to expose only read-only tools.

Missing required variables make the server exit with a clear error at startup rather than fail on the first API call.

SSE mode also exposes `GET /healthz`, an unauthenticated liveness endpoint that returns a small JSON response. It does not contact NPM or validate credentials; use it for container and reverse-proxy health checks only.

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

- `nginx_proxy_manager_mcp/server.py` validates required env vars, builds the FastMCP app, registers every tool module, and serves either SSE or stdio.
- `nginx_proxy_manager_mcp/npm_client.py` wraps `httpx`, exchanges the admin email/password for a JWT on first use, caches the token in memory, and re-authenticates on `401`.
- `nginx_proxy_manager_mcp/tools/` keeps one module per NPM resource. Adding a resource means adding one `register_*_tools(mcp, client)` function and one registration line.

## Development

```bash
python -m venv .venv
. .venv/bin/activate
pip install -e . -r requirements-dev.txt
pytest -q
```

Tests mock the NPM API with [respx](https://lundberg.github.io/respx/), so the suite runs offline and touches no real infrastructure. CI runs the same command on every push and pull request.

## Releases

Tagged releases (`vX.Y.Z`) publish the `nginx-proxy-manager-mcp-server` package to PyPI via trusted publishing (`.github/workflows/publish.yml`) and multi-architecture Docker images to GitHub Container Registry:

- `ghcr.io/euisuh/nginx-proxy-manager-mcp:<version>` for tags such as `v0.2.0`
- `ghcr.io/euisuh/nginx-proxy-manager-mcp:<major>.<minor>` for semver tags
- `ghcr.io/euisuh/nginx-proxy-manager-mcp:latest` for the newest tagged release

The Docker workflow also builds pull requests without pushing an image, so packaging changes are validated before release.

## Security

Anything that can reach this MCP server has admin-level control over your proxy hosts and certificates.

- Do not expose the MCP endpoint publicly.
- Keep the Docker port bound to `127.0.0.1` unless you have another trusted network boundary.
- Bare SSE runs bind to `127.0.0.1` by default; set `MCP_HOST=0.0.0.0` only behind a trusted network boundary.
- Set `MCP_BEARER_TOKEN` for SSE deployments that can be reached by anything beyond the local machine, and configure clients to send `Authorization: Bearer YOUR_TOKEN`.
- Use environment variables or a secrets manager for NPM credentials; do not commit `.env`.
- The NPM admin JWT lives in process memory and is never written to disk.
- The container runs as a non-root user.

See [SECURITY.md](SECURITY.md) for reporting and deployment guidance.

## Roadmap

See [ROADMAP.md](ROADMAP.md). Near-term priorities are PyPI publishing, MCP directory submission, broader NPM resource coverage, and integration tests.

## Directory metadata

- [`smithery.yaml`](smithery.yaml) describes stdio launch configuration for Smithery-style MCP directories.
- [`glama.json`](glama.json) declares the repository maintainer for Glama MCP registry verification.

## Limitations

- Covers proxy hosts, redirection hosts, streams, certificates, and access lists only. 404 hosts, users, audit log, and settings are not implemented yet.
- Certificate creation supports Let's Encrypt HTTP-01 only — no DNS-01 challenge and no custom certificate upload yet.
- One NPM instance per server process; there is no multi-tenant or multi-host routing.
- Optional SSE bearer-token auth protects the HTTP endpoint, but there is no per-tool authorization after a client is authenticated.
- `/healthz` reports only process liveness, not NPM reachability.
- Written against the NPM v2 API; older or forked NPM builds may differ.

## Contributing

Issues and pull requests are welcome. See [CONTRIBUTING.md](CONTRIBUTING.md). Adding a new NPM resource follows a fixed shape:

1. Create `nginx_proxy_manager_mcp/tools/<resource>.py` with a `register_<resource>_tools(mcp, client)` function.
2. Register it in `build_server()` in `nginx_proxy_manager_mcp/server.py`.
3. Add `tests/test_<resource>.py` covering each tool with respx-mocked NPM responses.
4. Run `ruff check .` and `pytest -q`.

Commits follow [Conventional Commits](https://www.conventionalcommits.org/).

## Author

Built and maintained by [Euisuh Jeong](https://github.com/euisuh) to manage a homelab reverse proxy from Claude Code.

## License

MIT — see [LICENSE](LICENSE).
