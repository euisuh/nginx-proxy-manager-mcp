# Nginx Proxy Manager MCP

<!-- mcp-name: io.github.euisuh/nginx-proxy-manager-mcp -->

[![CI](https://github.com/euisuh/nginx-proxy-manager-mcp/actions/workflows/ci.yml/badge.svg)](https://github.com/euisuh/nginx-proxy-manager-mcp/actions/workflows/ci.yml)
[![Docker](https://github.com/euisuh/nginx-proxy-manager-mcp/actions/workflows/docker.yml/badge.svg)](https://github.com/euisuh/nginx-proxy-manager-mcp/actions/workflows/docker.yml)
[![Python Package](https://github.com/euisuh/nginx-proxy-manager-mcp/actions/workflows/python-package.yml/badge.svg)](https://github.com/euisuh/nginx-proxy-manager-mcp/actions/workflows/python-package.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

An MCP server for [Nginx Proxy Manager](https://nginxproxymanager.com/). It lets Claude and other MCP clients manage proxy hosts, redirection hosts, TCP/UDP streams, Let's Encrypt certificates, and access lists through typed tools instead of clicking through the NPM admin UI.

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

- 34 MCP tools for common NPM operations (table below).
- `dry_run` on all mutating tools to preview NPM requests before applying them.
- One-shot `create_proxy_host_with_letsencrypt` requests a certificate, then creates an HTTPS-forced proxy host.
- Let's Encrypt over HTTP-01 or DNS-01 (wildcards), with the request shape picked from the NPM version reported by `GET /api/`.
- `NPM_READ_ONLY=true` registers only the 12 `list_`/`get_`/`find_` tools.
- JWT auth against the NPM API with in-memory token caching and automatic re-authentication on `401`.
- Docker sidecar deployment that binds the MCP port to localhost by default.
- Offline pytest suite with mocked NPM API responses, including end-to-end calls through the MCP protocol layer; CI runs it on Python 3.10–3.13.
- Ruff quality gate and contributor templates for public maintenance.
- Python wheel build validation and MCP directory metadata for promotion readiness.
- No token persistence and no hardcoded credentials.

## Tools

<!-- tools:start -->
| Tool | Category | Read-only | Description |
|---|---|---|---|
| `list_proxy_hosts` | Proxy hosts | yes | List proxy hosts configured in NPM, including their current status. |
| `get_proxy_host` | Proxy hosts | yes | Fetch one proxy host by ID, including its configured fields and current status. |
| `create_proxy_host` | Proxy hosts |  | Create a proxy host that routes the supplied domains to an HTTP or HTTPS upstream. |
| `create_proxy_host_with_letsencrypt` | Proxy hosts |  | Request a Let's Encrypt certificate, then create a proxy host using that certificate with HTTPS forced. |
| `update_proxy_host` | Proxy hosts |  | Update writable settings on an existing proxy host by ID. |
| `delete_proxy_host` | Proxy hosts |  | Permanently delete a proxy host by ID, removing its configured domain routing from NPM. |
| `enable_proxy_host` | Proxy hosts |  | Enable a disabled proxy host by ID so NPM serves its configured domain routing again. |
| `disable_proxy_host` | Proxy hosts |  | Disable a proxy host by ID while retaining its configuration. |
| `list_certificates` | Certificates | yes | List SSL certificates known to NPM, including expiry information when provided by NPM. |
| `get_certificate` | Certificates | yes | Fetch one certificate by ID, including provider, domain names, expiry and meta. |
| `create_letsencrypt_cert` | Certificates |  | Request a new Let's Encrypt certificate for the supplied domains, over HTTP-01 by default or DNS-01 with dns_challenge=True (required for wildcards). |
| `delete_certificate` | Certificates |  | Permanently delete a certificate by ID, for example one left behind when create_proxy_host_with_letsencrypt fails at the proxy step. |
| `renew_certificate` | Certificates |  | Request renewal of an existing certificate by ID. |
| `list_access_lists` | Access lists | yes | List access lists configured in NPM. |
| `get_access_list` | Access lists | yes | Fetch one access list by ID, including its client rules and basic-auth user metadata. |
| `create_access_list` | Access lists |  | Create an access list containing optional IP allow/deny rules and basic-auth users. |
| `update_access_list` | Access lists |  | Update writable fields on an existing access list by ID, including client rules and basic-auth users. |
| `delete_access_list` | Access lists |  | Permanently delete an access list by ID from NPM. |
| `list_redirection_hosts` | Redirection hosts | yes | List configured redirection hosts and their current status. |
| `get_redirection_host` | Redirection hosts | yes | Fetch one redirection host by ID with its configured destination and status. |
| `create_redirection_host` | Redirection hosts |  | Create a host that redirects requests for domains to a destination using the selected HTTP status. |
| `update_redirection_host` | Redirection hosts |  | Update writable settings on an existing redirection host by ID. |
| `delete_redirection_host` | Redirection hosts |  | Permanently delete a redirection host by ID, removing its redirect configuration from NPM. |
| `enable_redirection_host` | Redirection hosts |  | Enable a disabled redirection host by ID so NPM serves its redirect again. |
| `disable_redirection_host` | Redirection hosts |  | Disable a redirection host by ID while keeping its configuration in NPM. |
| `list_streams` | Streams | yes | List configured TCP/UDP streams and their current status. |
| `get_stream` | Streams | yes | Fetch one TCP/UDP stream by ID, including its forwarding ports and protocol settings. |
| `create_stream` | Streams |  | Create a TCP/UDP port forward from an incoming port to a destination host and port. |
| `update_stream` | Streams |  | Update writable port, destination, or protocol fields on an existing stream by ID. |
| `delete_stream` | Streams |  | Permanently delete a TCP/UDP stream by ID; NPM stops forwarding that port immediately and this cannot be undone. |
| `enable_stream` | Streams |  | Enable a disabled TCP/UDP stream by ID so NPM forwards its incoming port again. |
| `disable_stream` | Streams |  | Disable a TCP/UDP stream by ID while retaining its forwarding configuration. |
| `find_host_by_domain` | Diagnostics | yes | Find proxy hosts, redirection hosts, and certificates serving a domain using exact or wildcard matching. |
| `list_expiring_certificates` | Diagnostics | yes | List certificates expiring within the requested UTC time window, including certificates already expired, sorted by expiry. |
<!-- tools:end -->

The table is generated by [`docs/tools_table.py`](docs/tools_table.py) from the registered tools; `tests/test_readme.py` fails if it drifts. Read-only tools are the ones `NPM_READ_ONLY` keeps.

List tools support optional server-side filtering after fetching from NPM: `domain` matches a case-insensitive substring in any domain name for proxy hosts, redirection hosts, and certificates; `enabled` filters proxy hosts, redirection hosts, and streams by status. All four accept `compact=True` to return only summary fields. Filters combine, and calls without arguments return the full, unchanged NPM list. For example, `list_proxy_hosts(domain="example", enabled=True, compact=True)` lists enabled hosts matching "example" with compact output.

All mutating tools expose `dry_run=True`. Previews contain `method` and `path`, plus `json` when the request has a body; the HTTPS workflow returns two previews in `steps`. The flag suppresses mutating requests, though some previews read current state. Update tools send only the fields in NPM's PUT schema (fixes [#19](https://github.com/euisuh/nginx-proxy-manager-mcp/issues/19)); this is covered by mocked tests and not yet checked against a live NPM instance.

## Compared to other NPM MCP servers

Competitor facts below come only from their linked READMEs fetched with `gh api repos/<owner>/nginx-proxy-manager-mcp/readme` on 2026-10-13. “not documented” means the README does not establish the capability, not that it is absent. Auth guard means inbound MCP client authentication, distinct from NPM API login.

| Repository | Tool count documented | Dry-run support | Transport | Auth guard |
|---|---:|---|---|---|
| [euisuh (this server)](https://github.com/euisuh/nginx-proxy-manager-mcp) | 34 | `dry_run` on all mutating tools | stdio, SSE | Optional SSE bearer token (`MCP_BEARER_TOKEN`); `/healthz` exempt |
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
# edit .env — NPM_EMAIL / NPM_PASSWORD of an existing NPM user (a dedicated non-admin user works; see Security)
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

Register the SSE server with Claude Code (without `--transport sse`, `claude mcp add` treats the URL as a command to run):

```bash
claude mcp add --transport sse npm http://localhost:8000/sse
# with MCP_BEARER_TOKEN set:
claude mcp add --transport sse npm http://localhost:8000/sse -H "Authorization: Bearer YOUR_TOKEN"
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

The published 0.6.0 wheel requires Python 3.12+; the source supports Python 3.10+.

Claude Desktop (`claude_desktop_config.json`) launching it with uvx:

```json
{
  "mcpServers": {
    "nginx-proxy-manager": {
      "command": "uvx",
      "args": ["nginx-proxy-manager-mcp-server"],
      "env": {
        "NPM_URL": "http://localhost:81",
        "NPM_EMAIL": "mcp@example.com",
        "NPM_PASSWORD": "...",
        "MCP_TRANSPORT": "stdio"
      }
    }
  }
}
```

Claude Code, same launch:

```bash
claude mcp add npm \
  -e NPM_URL=http://localhost:81 -e NPM_EMAIL=mcp@example.com -e NPM_PASSWORD=... \
  -e MCP_TRANSPORT=stdio \
  -- uvx nginx-proxy-manager-mcp-server
```

To check a launch without touching NPM, list tools: tool listing makes no NPM request, and NPM is contacted on the first tool call.

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
| `NPM_EMAIL` | yes | — | Email of the NPM user the server logs in as (see [NPM credential scope](#npm-credential-scope)) |
| `NPM_PASSWORD` | yes | — | That user's password |
| `NPM_READ_ONLY` | no | disabled | `1`, `true`, or `yes` (case-insensitive) registers only `list_`, `get_`, and `find_` tools; all other values disable read-only mode |
| `MCP_TRANSPORT` | no | `sse` | MCP transport: `sse` or `stdio` |
| `MCP_HOST` | no | `127.0.0.1` | Bind address for SSE mode; Docker Compose sets `0.0.0.0` inside the container while publishing only to localhost |
| `MCP_PORT` | no | `8000` | Bind port for SSE mode |
| `MCP_BEARER_TOKEN` | no | — | Optional bearer token required for SSE HTTP requests |

Set `NPM_READ_ONLY=true` to expose only read-only tools.

Missing required variables make the server exit with a clear error at startup rather than fail on the first API call.

SSE mode also exposes `GET /healthz`, an unauthenticated liveness endpoint that returns a small JSON response. It does not contact NPM or validate credentials; use it for container and reverse-proxy health checks only.

## NPM compatibility

Request bodies follow the JSON schemas in NPM's `backend/schema/` and were checked against tags v2.12.6, v2.13.0, and v2.16.0. NPM rejects unknown fields (`additionalProperties: false`), so version differences matter:

- NPM 2.13.0 removed `meta.letsencrypt_email` and `meta.letsencrypt_agree` and uses the NPM user's account email for Let's Encrypt. The server reads the version once from the unauthenticated `GET /api/` and only sends those fields to NPM older than 2.13; there, `email` is required.
- Update tools send only the fields in NPM's PUT schema (see [#19](https://github.com/euisuh/nginx-proxy-manager-mcp/issues/19)).

These checks are against schema files and mocked tests, not a live NPM instance.

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
- `nginx_proxy_manager_mcp/npm_client.py` wraps `httpx`, exchanges the email/password for a JWT on first use, caches the token in memory, and re-authenticates once on `401`. NPM errors become `NPMAPIError` with NPM's own message; transport failures become `NPMConnectionError` naming `NPM_URL`.
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

Anything that can reach this MCP server has the NPM permissions of the account in `NPM_EMAIL`, so it can change proxy hosts and certificates.

### NPM credential scope

The server needs no NPM admin rights. It only calls `/api/tokens`, `/api/nginx/*`, and the unauthenticated `GET /api/`. It never touches users, settings, or the audit log. Create a dedicated NPM user (Users → Add User) instead of reusing your admin login:

- Permissions are per resource: proxy hosts, redirection hosts, streams, access lists, and certificates, each `manage`, `view`, or `hidden` (NPM `permission-object.json`). Grant `manage` only where the assistant should make changes.
- Item visibility `all` lets the user see hosts created by others; `user` limits it to items it created.
- For an inspect-only setup, pair a `view`-only NPM user with `NPM_READ_ONLY=true`. NPM enforces the first and the server enforces the second.
- On NPM 2.13+, Let's Encrypt registers with this user's email, so give it a real address.

### Deployment

- Do not expose the MCP endpoint publicly.
- Keep the Docker port bound to `127.0.0.1` unless you have another trusted network boundary.
- Bare SSE runs bind to `127.0.0.1` by default; set `MCP_HOST=0.0.0.0` only behind a trusted network boundary.
- Set `MCP_BEARER_TOKEN` for SSE deployments that can be reached by anything beyond the local machine, and configure clients to send `Authorization: Bearer YOUR_TOKEN`.
- Use environment variables or a secrets manager for NPM credentials; do not commit `.env`.
- The NPM JWT lives in process memory, is sent only in the `Authorization` header, and is never logged or written to disk. Error messages carry NPM's error text and URL, not request headers or bodies.
- `create_letsencrypt_cert` with DNS-01 takes the DNS provider credentials as a tool argument, so they appear in the MCP client's transcript. NPM never returns them, and dry-run previews show `<redacted>`.
- `get_access_list` drops NPM's password `hint` field, which reveals the first character and length of each basic-auth password.
- The container runs as a non-root user.

See [SECURITY.md](SECURITY.md) for reporting and deployment guidance.

## Roadmap

See [ROADMAP.md](ROADMAP.md). Near-term priorities are PyPI publishing, MCP directory submission, broader NPM resource coverage, and integration tests.

## Directory metadata

- [`smithery.yaml`](smithery.yaml) describes stdio launch configuration for Smithery-style MCP directories.
- [`glama.json`](glama.json) declares the repository maintainer for Glama MCP registry verification.

## Limitations

- Covers proxy hosts, redirection hosts, streams, certificates, and access lists only. 404 hosts, users, audit log, and settings are not implemented.
- Certificates: Let's Encrypt (HTTP-01, or DNS-01 via a certbot DNS plugin NPM knows). No custom certificate upload or download.
- `update_access_list` replaces basic-auth users wholesale when `items` is given, and each item needs its password (NPM cannot return stored passwords).
- No integration test against a live NPM container; request shapes are checked against NPM's schema files and mocked tests.
- One NPM instance per server process; there is no multi-tenant or multi-host routing.
- Optional SSE bearer-token auth protects the HTTP endpoint, but there is no per-tool authorization after a client is authenticated.
- `/healthz` reports only process liveness, not NPM reachability.
- Written against the NPM v2 API; older or forked NPM builds may differ.

## Contributing

Issues and pull requests are welcome. See [CONTRIBUTING.md](CONTRIBUTING.md). Adding a new NPM resource follows a fixed shape:

1. Create `nginx_proxy_manager_mcp/tools/<resource>.py` with a `register_<resource>_tools(mcp, client)` function.
2. Register it in `register_all()` in `nginx_proxy_manager_mcp/server.py`.
3. Add `tests/test_<resource>.py` covering each tool with respx-mocked NPM responses.
4. Regenerate the README tool table with `python docs/tools_table.py`.
5. Run `ruff check .` and `pytest -q`.

Commits follow [Conventional Commits](https://www.conventionalcommits.org/).

## Author

Built and maintained by [Euisuh Jeong](https://github.com/euisuh) to manage a homelab reverse proxy from Claude Code.

## License

MIT — see [LICENSE](LICENSE).
