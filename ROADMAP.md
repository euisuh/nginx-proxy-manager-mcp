# Roadmap

This project is intentionally small: one MCP server that gives AI assistants safe, typed access to Nginx Proxy Manager. The roadmap focuses on making that use case reliable enough for real homelabs and clear enough for outside contributors.

## v0.2 — Safer day-to-day proxy automation

- Add dry-run/preview output for mutating tools.
- Add input validation for domain names, schemes, ports, and certificate IDs before hitting the NPM API.
- Add a `create_proxy_host_with_certificate` workflow tool for the common “subdomain → service → HTTPS” path.
- Improve error messages from NPM API responses so MCP clients can recover instead of returning opaque HTTP errors.

## v0.3 — Broader NPM resource coverage

- 404 hosts and dead hosts.
- Custom certificates: upload/list/renew/delete where supported by the NPM API.
- Users and audit-log read-only tools.

## v0.4 — Distribution and deployment polish

- Publish a versioned container image to GitHub Container Registry.
- Add Smithery/Glama-compatible metadata if the project is accepted by those MCP directories.
- Add a minimal `pipx`/stdio installation path for users who do not want Docker.
- Add example Claude Desktop, Claude Code, Cursor, and Windsurf configuration snippets.

## v0.5 — Operational hardening

- Optional allowlist for destructive tools.
- Optional shared bearer token in front of the MCP endpoint.
- Structured logs with request IDs and redacted credentials.
- Health/readiness endpoint for the SSE sidecar.
- Integration test profile against an ephemeral NPM container.

## Positioning

The public name is `nginx-proxy-manager-mcp` so the repository matches the exact product and search terms people use. Keep README, container image names, MCP directory submissions, and release assets aligned with that name.
