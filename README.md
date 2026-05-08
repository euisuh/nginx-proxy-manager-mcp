# npm-mcp

Lightweight MCP server for [Nginx Proxy Manager](https://nginxproxymanager.com/). Runs as a Docker sidecar and exposes 15 tools for managing proxy hosts, SSL certificates, and access lists.

## Tools

| Category | Tools |
|---|---|
| Proxy hosts | `list_proxy_hosts`, `get_proxy_host`, `create_proxy_host`, `update_proxy_host`, `delete_proxy_host`, `enable_proxy_host`, `disable_proxy_host` |
| SSL certs | `list_certificates`, `create_letsencrypt_cert`, `renew_certificate` |
| Access lists | `list_access_lists`, `get_access_list`, `create_access_list`, `update_access_list`, `delete_access_list` |

## Setup

**1. Copy env template:**

```bash
cp .env.example .env
```

Edit `.env`:

```
NPM_EMAIL=your-admin@email.com
NPM_PASSWORD=your-npm-password
```

`NPM_URL` defaults to `http://app:81` (internal Docker network) — leave as-is if npm-mcp runs in the same compose stack.

**2. Start both services:**

```bash
docker compose up -d
```

## Connecting to Claude Code

Add to your MCP settings (run in terminal):

```bash
claude mcp add npm http://localhost:8000/sse
```

Or add manually to `~/.claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "npm": {
      "url": "http://localhost:8000/sse"
    }
  }
}
```

## Development

```bash
cd mcp
pip install -r requirements.txt -r requirements-dev.txt
cd ..
pytest tests/ -v
```

## Security

- Credentials injected via env vars only — never hardcoded
- MCP port bound to `127.0.0.1` only — not exposed to the internet
- NPM admin token stored in memory, not on disk
- `.env` is gitignored

## Architecture

```
Claude ──MCP──► npm-mcp (port 8000) ──HTTP+JWT──► NPM API (port 81)
```
